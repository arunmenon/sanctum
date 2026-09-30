"""Shadow prompt ablation for System One decisions (prompt review rows 1 to 10). Dev only.

One call = one row variant: a decision (d2, d6, d4), a template id and a provider. Answers are
collected in shadow (no calibration is ever applied), labelled on the evaluator side, and reported
with denominators and uncertainty:

- d6 / d4: collected through the normal runner and broker (`--round3 <d> --round3-template <t>`);
  labels from `sanctum_eval.calibration_labels`; D6 stratified by rule-flagged versus promotable
  candidate pairs.
- d2: one direct call per dev case with the template's descriptor set (the broker's state shape);
  labels are counterfactual (recall drops when the hub's manifest is removed, C1-fair runs, local),
  cached per commit.

Every noul template gets nested case-grouped CV (`sanctum_eval.calibration.nested_cv`) with a band
chosen on inner out-of-fold predictions at the unchanged tolerance and evaluated on outer folds.
Diagnostic templates (choice, score, decomposition, negative polarity) are reported as signals only.

Spend: a campaign ledger (docs/reports/data/campaign-ledger.json) holds every row's calls and
tokens; each run's ceilings are the smaller of its own and what the campaign has left, and they are
enforced before every HTTP attempt.
"""
import argparse
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from sanctum_eval.calibration import group_folds, nested_cv, records_from_fit, wilson
from sanctum_eval.calibration_labels import labels_from_run, relation_types_from_run
from sanctum_ref.providers import d2_request
from sanctum_ref.providers.http_systemone import d2_questions
from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import DEFAULT_HUBS_CONFIG, DEFAULT_WORLD_BUILD, RunConfig, git_state, load_cases, public_request, run
from sanctum_run.gateway import released_hub_ids
from sanctum_run.system_one_broker import state_sources
from sanctum_systemone import CampaignBudget, SystemOneClient, load_provider_specs, set_campaign_budget
from tools.fit_system_one import choose_skip_band, choose_use_band
from tools.measure_system_one_batches import dotenv

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "reports" / "data" / "campaign-ledger.json"
# owner ceiling (raised twice: 470/420k/45k, then 600/560k/60k, now 800/760k/80k), pre-dispatch enforced
CAMPAIGN = {"typesafe-jev": {"calls": 800, "input_tokens": 760_000, "output_tokens": 80_000}}
FLAGGED_SEED = 20260930


# ---- metrics ------------------------------------------------------------------------------------
def roc_auc(pairs):
    positives = [p for p, y in pairs if y]
    negatives = [p for p, y in pairs if not y]
    if not positives or not negatives:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives) / (len(positives) * len(negatives))


def pr_auc(pairs):
    total = sum(y for _, y in pairs)
    if not total:
        return None
    hits, area = 0, 0.0
    for index, (_, y) in enumerate(sorted(pairs, key=lambda pair: -pair[0]), start=1):
        if y:
            hits += 1
            area += hits / index
    return area / total


def summary(pairs, probability=True):
    out = {"n": len(pairs), "positives": sum(y for _, y in pairs)}
    auc, ap = roc_auc(pairs), pr_auc(pairs)
    out["roc_auc"] = None if auc is None else round(auc, 4)
    out["pr_auc"] = None if ap is None else round(ap, 4)
    if probability and pairs:
        out["brier_raw"] = round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 4)
    return out


def rounded(value):
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {k: rounded(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [rounded(v) for v in value]
    return value


# ---- ledger -------------------------------------------------------------------------------------
def ledger() -> dict:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"rows": []}


def remaining(provider: str) -> Optional[dict]:
    ceiling = CAMPAIGN.get(provider)
    if ceiling is None:
        return None
    spent = {key: sum(row.get(key, 0) for row in ledger()["rows"] if row["provider"] == provider) for key in ceiling}
    return {key: ceiling[key] - spent[key] for key in ceiling}


def record(row: dict) -> None:
    data = ledger()
    data["rows"].append(row)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")


def leaf_errors(error: BaseException, depth: int = 0) -> list[str]:
    """The innermost exceptions of a (possibly nested) exception group, with their last frames."""
    import traceback
    if isinstance(error, BaseExceptionGroup):
        return [line for inner in error.exceptions for line in leaf_errors(inner, depth + 1)]
    frames = traceback.extract_tb(error.__traceback__)[-3:]
    where = " <- ".join(f"{Path(f.filename).name}:{f.lineno} {f.name}" for f in reversed(frames))
    cause = f" (cause: {type(error.__cause__).__name__}: {error.__cause__})" if error.__cause__ else ""
    return [f"{type(error).__name__}: {error} at {where}{cause}"]


# ---- signals --------------------------------------------------------------------------------------
def signals(template, answers: dict, qid: str) -> dict:
    """Named numeric signals from one item's answers. Only `p` (a positive-polarity noul) may ever
    be calibrated; everything else is diagnostic."""
    out = {}
    if template.subquestions:
        for name in template.subquestions:
            answer = answers.get(f"{qid}#{name}") or {}
            if answer.get("type") == "noul":
                out[name] = answer["noul"]
        if len(out) == len(template.subquestions):
            out["product_diagnostic"] = math.prod(out.values())
        return out
    answer = answers.get(qid) or {}
    if answer.get("type") == "noul":
        key = "p" if template.polarity == "positive" and not template.diagnostic else "p_diagnostic"
        out[key] = answer["noul"] if template.polarity == "positive" else 1 - answer["noul"]
    elif answer.get("type") == "choice":
        probabilities = answer.get("probabilities") or {}
        out["p_relation_diagnostic"] = 1 - probabilities.get("no_conflict", 0.0)
        out["choice"] = answer.get("choice")
    elif answer.get("type") == "score":
        out["score_diagnostic"] = answer["score"] / 3.0
    return out


# ---- collection -------------------------------------------------------------------------------------
def collect_round3(arguments, template, run_dir: Path):
    empty = run_dir.parent / "no-calibration"
    empty.mkdir(exist_ok=True)
    result = run(ProcessSUT(["--config", "C4", "--round3", arguments.decision, "--round3-provider", arguments.provider,
                             "--round3-template", template.id, "--calibration-dir", str(empty)]),
                 RunConfig(cases_dir=arguments.cases, out_dir=run_dir, seed=20260930, sut_name="ref",
                           config_id=f"C4+{arguments.decision.upper()}", world_build_dir=arguments.world_build,
                           system_one_provider=arguments.provider, system_one_profile="relaxed"))
    items, models, outcomes, unavailable = {}, set(), {}, 0
    receipts = [json.loads(line) for line in (result.out_dir / "receipts.jsonl").read_text().splitlines()]
    traces = [json.loads(line) for line in (result.out_dir / "traces.jsonl").read_text().splitlines()]
    for case_id, receipt, trace in zip(result.manifest["cases"], receipts, traces):
        for call in trace.get("model_calls") or []:
            key = call.get("reason") or "ok"
            outcomes[key] = outcomes.get(key, 0) + 1
        for decision in receipt["decisions"]:
            value = decision.get("value")
            target = str(decision.get("target", ""))
            if value is None:
                unavailable += target.startswith(arguments.decision)
                continue
            item = str(value.get("item", ""))
            if not item.startswith(f"{arguments.decision}:"):
                continue
            models.add(decision.get("model_version"))
            items[(case_id, item.split(":", 1)[1])] = {
                "signals": signals(template, value.get("answers") or {}, item),
                "rule_flagged": bool(value.get("rule_flagged")), "refs": value.get("refs")}
    labels = labels_from_run(arguments.decision, result.out_dir, arguments.cases)
    relation_types = relation_types_from_run(result.out_dir, arguments.cases) if arguments.decision == "d6" else {}
    return items, labels, relation_types, sorted(map(str, models)), outcomes, unavailable


def d2_labels(arguments) -> dict:
    """Counterfactual D2 labels (local C1-fair runs, no provider calls), cached per commit."""
    cache = arguments.scratch / f"d2-labels-{git_state()['git_commit'][:12]}.json"
    if cache.exists():
        return {tuple(key.split("\t")): value for key, value in json.loads(cache.read_text()).items()}
    from tools.fit_d2_standin import recalls
    manifests = ROOT / "owners" / "manifests"
    labels = {}
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        full = recalls(arguments.cases, scratch / "full", manifests, arguments.world_build)
        for hub in ("codehub", "dochub", "memoryhub", "skillhub"):
            registry = scratch / f"without-{hub}"
            shutil.copytree(manifests, registry)
            (registry / f"{hub}.yaml").unlink()
            without = recalls(arguments.cases, scratch / f"run-{hub}", registry, arguments.world_build)
            for case_id, recall in full.items():
                labels[(case_id, hub)] = int(without.get(case_id, recall) < recall - 1e-9)
    cache.write_text(json.dumps({"\t".join(key): value for key, value in labels.items()}))
    return labels


def collect_d2(arguments, template):
    spec = load_provider_specs(ROOT / "configs" / "system_one_providers.yaml")[arguments.provider]
    environment = {**dotenv(), **os.environ}
    descriptor_file = ROOT / (template.descriptors or "configs/d2_standin.yaml")
    descriptors = state_sources(yaml.safe_load(descriptor_file.read_text())["descriptors"],
                                released_hub_ids(DEFAULT_HUBS_CONFIG))
    client = SystemOneClient(spec, spec.resolved_base_url(environment) or "https://api.typesafe.ai",
                             spec.requested_model(environment),
                             api_key=environment.get(spec.api_key_env) if spec.api_key_env else None)
    items, models, outcomes, unavailable = {}, set(), {}, 0
    for gold in load_cases(arguments.cases):
        query = public_request(gold).query
        requests = [d2_request(hub, query, 60000) for hub in descriptors]
        outcome = client.decide({"query": query, "sources": descriptors}, d2_questions(requests, template), 60.0,
                                max_calls=len(descriptors))          # one per source on one-question providers
        key = outcome.unavailable_reason.value if outcome.unavailable_reason else "ok"
        outcomes[key] = outcomes.get(key, 0) + 1
        if outcome.model:
            models.add(outcome.model)
        for hub in descriptors:
            qid = f"d2:{hub}"
            if qid in outcome.answers:
                items[(gold.case_id, hub)] = {"signals": signals(template, outcome.answers, qid), "rule_flagged": False}
            else:
                unavailable += 1
    client.close()
    return items, d2_labels(arguments), {}, sorted(models), outcomes, unavailable


# ---- evaluation -------------------------------------------------------------------------------------
def nested_with_bands(decision, raw, labels, flagged, tolerance, sources=None):
    """nested_cv with the decision's band rule; for D6 promotions are counted on candidates only.
    `sources` ({key: source_id}) enables per-source intercepts (D2 keys carry the source already)."""
    source_of = (lambda key: key[1]) if decision == "d2" else ((lambda key: sources.get(key, "")) if sources else None)
    records = records_from_fit(raw, labels, source_of=source_of)
    calibrators = ("platt", "platt_l2", "intercept_only", "source_intercepts") if source_of else \
        ("platt", "platt_l2", "intercept_only")
    parts = group_folds(records, 5, 20260930)
    usable = [k for k, held in enumerate(parts)
              if held and len({r.label for j, part in enumerate(parts) if j != k for r in part}) >= 2]
    order = iter(usable)
    keys_by_record = {id(r): key for r, key in zip(records, sorted(set(raw) & set(labels)))}

    def band_fit(probabilities, fold_labels):
        pairs = list(zip(probabilities, fold_labels))
        return choose_skip_band(pairs, tolerance) if decision == "d2" else choose_use_band(pairs, tolerance)

    def band_eval(band, probabilities, fold_labels):
        held = parts[next(order)]
        if decision == "d2":
            skipped = [(p, y) for p, y in zip(probabilities, fold_labels) if p < band]
            return {"band": band, "skipped": len(skipped), "harmful_skips": sum(y for _, y in skipped),
                    "judgments": len(fold_labels)}
        rows = [(p, y, flagged.get(keys_by_record[id(r)], False)) for p, y, r in zip(probabilities, fold_labels, held)]
        eligible = [(p, y) for p, y, is_flagged in rows if not is_flagged or decision == "d4"]
        promoted = [(p, y) for p, y in eligible if band < 1.0 and p >= band]
        return {"band": band, "eligible": len(eligible), "promoted": len(promoted),
                "false_promotions": sum(1 - y for _, y in promoted)}

    result = nested_cv(records, calibrators, outer_folds=5, inner_folds=4, seed=20260930,
                       band_fit=band_fit, band_eval=band_eval)
    folds = [dict(f.band_metrics, calibrator=f.calibrator, n=f.n, positives=f.positives) for f in result.folds]
    totals = {}
    for fold in folds:
        for key in ("skipped", "harmful_skips", "judgments", "eligible", "promoted", "false_promotions"):
            if key in fold:
                totals[key] = totals.get(key, 0) + fold[key]
    if "promoted" in totals:
        totals["false_promotion_rate_wilson95"] = wilson(totals["false_promotions"], totals["promoted"])
    if "skipped" in totals:
        totals["harmful_skip_rate_wilson95"] = wilson(totals["harmful_skips"], totals["skipped"])
    return {"summary": result.summary(), "folds": folds, "totals": totals, "diagnostic": result.diagnostic}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row", required=True, help="campaign row label, e.g. 3 or 6")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--decision", required=True, choices=["d2", "d6", "d4"])
    parser.add_argument("--template", required=True)
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "dev")
    parser.add_argument("--max-calls", type=int, required=True)
    parser.add_argument("--max-input-tokens", type=int, required=True)
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument("--tolerance", type=float, default=None, help="default: 0.2 for d6/d4, 0.05 for d2")
    parser.add_argument("--world-build", type=Path, default=DEFAULT_WORLD_BUILD)
    parser.add_argument("--scratch", type=Path, required=True, help="kept run directories and caches")
    parser.add_argument("--expect-world", default=None, help="required world manifest prefix; checked before any call")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    if any(part in str(arguments.cases.resolve()) for part in ("holdout", "acceptance")):
        raise SystemExit("ablation runs on dev only")
    tolerance = arguments.tolerance if arguments.tolerance is not None else (0.05 if arguments.decision == "d2" else 0.2)
    template = TemplateRegistry(DEFAULT_TEMPLATES).resolve(arguments.decision, arguments.provider, arguments.template)
    left = remaining(arguments.provider)
    calls, input_tokens, output_tokens = arguments.max_calls, arguments.max_input_tokens, arguments.max_output_tokens
    if left is not None:
        calls, input_tokens = min(calls, left["calls"]), min(input_tokens, left["input_tokens"])
        output_tokens = min(output_tokens or left["output_tokens"], left["output_tokens"])
        if calls <= 0 or input_tokens <= 0 or output_tokens <= 0:
            raise SystemExit(f"campaign ceiling reached for {arguments.provider}: {left}")
    campaign = CampaignBudget(calls, input_tokens, output_tokens)
    set_campaign_budget(campaign)
    arguments.scratch.mkdir(parents=True, exist_ok=True)
    run_dir = arguments.scratch / f"row{arguments.row}-{arguments.provider}-{template.id}"
    import hashlib
    world_manifest = hashlib.sha256((arguments.world_build / "manifest.json").read_bytes()).hexdigest()[:16]
    if arguments.expect_world and not world_manifest.startswith(arguments.expect_world):
        raise SystemExit(f"world manifest {world_manifest} is not the expected {arguments.expect_world}; no call made")
    failure = None
    try:
        if arguments.decision == "d2":
            items, labels, relation_types, models, outcomes, unavailable = collect_d2(arguments, template)
        else:
            if run_dir.exists():
                shutil.rmtree(run_dir)
            items, labels, relation_types, models, outcomes, unavailable = collect_round3(arguments, template, run_dir)
    except BaseException as error:                    # spend is recorded even when collection fails
        failure = error
        raise SystemExit("collection failed:\n" + "\n".join(leaf_errors(error)))
    finally:
        record({"row": arguments.row, "provider": arguments.provider, "template": template.id,
                "world_manifest": world_manifest, **campaign.summary(),
                **({"note": f"failed: {type(failure).__name__}"} if failure else {})})
    keys = sorted(k for k in items if k in labels)
    flagged = {k: items[k]["rule_flagged"] for k in keys}
    signal_names = sorted({name for k in keys for name, value in items[k]["signals"].items() if isinstance(value, (int, float))})
    per_signal = {}
    for name in signal_names:
        pairs = [(items[k]["signals"][name], labels[k]) for k in keys if name in items[k]["signals"]]
        probability = name != "score_diagnostic"
        entry = {"all": summary(pairs, probability)}
        if arguments.decision == "d6":
            entry["rule_flagged"] = summary([(items[k]["signals"][name], labels[k]) for k in keys
                                             if name in items[k]["signals"] and flagged[k]], probability)
            entry["candidates"] = summary([(items[k]["signals"][name], labels[k]) for k in keys
                                           if name in items[k]["signals"] and not flagged[k]], probability)
        per_signal[name] = entry
    report = {
        "row": arguments.row, "provider": arguments.provider, "decision": arguments.decision, "template": template.id,
        "world_manifest": world_manifest,
        "diagnostic": template.diagnostic, "state": template.state, "models": models,
        "items_answered": len(items), "items_labelled": len(keys), "items_unavailable": unavailable,
        "model_call_outcomes": outcomes, "campaign_row": campaign.summary(), "ceilings": {"calls": calls, "input_tokens": input_tokens},
        "tolerance": tolerance, "signals": per_signal, "git_commit": git_state()["git_commit"],
    }
    sources = {k: (items[k].get("refs") or [{}])[0].get("source_id", "") for k in keys} if arguments.decision == "d4" else None
    if "p" in signal_names and not template.diagnostic and any(labels[k] for k in keys):
        raw = {k: items[k]["signals"]["p"] for k in keys if "p" in items[k]["signals"]}
        report["nested_cv"] = nested_with_bands(arguments.decision, raw, labels, flagged, tolerance, sources)
    if arguments.decision in ("d2", "d4") and any(labels[k] for k in keys):
        # source-prior-only control: every raw p = 0.5, so only per-source intercepts can separate
        report["control_source_prior"] = nested_with_bands(arguments.decision, {k: 0.5 for k in keys}, labels,
                                                           flagged, tolerance, sources)
    if relation_types and "choice" in {n for k in keys for n in items[k]["signals"]}:
        typed = [(items[k]["signals"].get("choice"), relation_types.get(k)) for k in keys if relation_types.get(k)]
        report["relation_type_accuracy"] = {"n": len(typed), "correct": sum(1 for c, t in typed if c == t),
                                            "wilson95": wilson(sum(1 for c, t in typed if c == t), len(typed))}
    report["items"] = {f"{k[0]}\t{k[1]}": {"label": labels[k], **items[k]} for k in keys}
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(rounded(report), indent=1, sort_keys=True) + "\n")
    print(json.dumps(rounded({k: report[k] for k in ("row", "provider", "template", "items_answered", "items_labelled",
                                                    "campaign_row", "model_call_outcomes")})))


if __name__ == "__main__":
    main()
