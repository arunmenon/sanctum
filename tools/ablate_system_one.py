"""Shadow prompt ablation for one System One decision and template (prompt review, rows 1-3).

Collects raw answers on dev through the normal runner and broker (shadow-only: no calibration
directory), labels them on the evaluator side (sanctum_eval.calibration_labels) and reports raw
discrimination and calibration, stratified for D6 by rule-flagged versus promotable candidate
pairs, plus a nested case-grouped CV check of whether any candidate pair clears a calibrated use
band at the false-promotion tolerance. The campaign ceiling is enforced before every HTTP attempt.

    PYTHONPATH=src:. python tools/ablate_system_one.py --provider typesafe-jev --decision d6 \\
        --template d6-noul-v2-relations --max-calls 30 --max-input-tokens 40000 --out results.json
"""
import argparse
import json
import math
import random
import tempfile
from pathlib import Path

from sanctum_eval.calibration_labels import labels_from_run
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import DEFAULT_WORLD_BUILD, RunConfig, git_state, run
from sanctum_systemone import CampaignBudget, set_campaign_budget
from tools.fit_system_one import brier, choose_use_band, logit, platt

ROOT = Path(__file__).resolve().parents[1]


def roc_auc(pairs):
    positives = [p for p, y in pairs if y]
    negatives = [p for p, y in pairs if not y]
    if not positives or not negatives:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def pr_auc(pairs):
    """Average precision (step-wise area under the precision-recall curve)."""
    total_positive = sum(y for _, y in pairs)
    if not total_positive:
        return None
    ranked = sorted(pairs, key=lambda pair: -pair[0])
    hits, area = 0, 0.0
    for index, (_, y) in enumerate(ranked, start=1):
        if y:
            hits += 1
            area += hits / index
    return area / total_positive


def summary(pairs):
    return {"n": len(pairs), "positives": sum(y for _, y in pairs),
            "roc_auc": None if roc_auc(pairs) is None else round(roc_auc(pairs), 4),
            "pr_auc": None if pr_auc(pairs) is None else round(pr_auc(pairs), 4),
            "brier_raw": round(brier(pairs), 4) if pairs else None}


def nested_band_check(keys, raw, labels, flagged, tolerance, outer=5, inner=4, seed=20260930):
    """Outer folds assess; inner folds (case-grouped) pick the use band; Platt is fitted on the
    outer-train cases. Counts candidate promotions and false promotions on outer-test cases."""
    cases = sorted({case for case, _ in keys})
    random.Random(seed).shuffle(cases)
    folds = [set(cases[i::outer]) for i in range(outer)]
    promoted = false = 0
    bands = []
    for fold in folds:
        train = [k for k in keys if k[0] not in fold]
        test = [k for k in keys if k[0] in fold]
        train_cases = sorted({case for case, _ in train})
        inner_folds = [set(train_cases[i::inner]) for i in range(inner)]
        held = []
        for inner_fold in inner_folds:
            fit_keys = [k for k in train if k[0] not in inner_fold]
            if not fit_keys or not any(labels[k] for k in fit_keys):
                continue
            a, b = platt([(logit(raw[k]), labels[k]) for k in fit_keys])
            held += [(1 / (1 + math.exp(-(a * logit(raw[k]) + b))), labels[k]) for k in train if k[0] in inner_fold]
        band = choose_use_band(held, tolerance) if held else 1.0
        bands.append(band)
        if band >= 1.0 or not any(labels[k] for k in train):
            continue
        a, b = platt([(logit(raw[k]), labels[k]) for k in train])
        for k in test:
            if flagged.get(k):
                continue                                   # only candidate pairs can be promoted
            p = 1 / (1 + math.exp(-(a * logit(raw[k]) + b)))
            if p >= band:
                promoted += 1
                false += 1 - labels[k]
    return {"outer_folds": outer, "inner_folds": inner, "bands": bands,
            "candidate_promotions": promoted, "false_candidate_promotions": false}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--decision", default="d6", choices=["d6", "d4"])
    parser.add_argument("--template", required=True)
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "dev")
    parser.add_argument("--max-calls", type=int, required=True)
    parser.add_argument("--max-input-tokens", type=int, required=True)
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument("--tolerance", type=float, default=0.2)
    parser.add_argument("--world-build", type=Path, default=DEFAULT_WORLD_BUILD)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    if any(part in str(arguments.cases.resolve()) for part in ("holdout", "acceptance")):
        raise SystemExit("ablation runs on dev only")
    campaign = CampaignBudget(arguments.max_calls, arguments.max_input_tokens, arguments.max_output_tokens)
    set_campaign_budget(campaign)
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        (scratch / "none").mkdir()
        result = run(ProcessSUT(["--config", "C4", "--round3", arguments.decision, "--round3-provider", arguments.provider,
                                 "--round3-template", arguments.template, "--calibration-dir", str(scratch / "none")]),
                     RunConfig(cases_dir=arguments.cases, out_dir=scratch / "collect", seed=20260930, sut_name="ref",
                               config_id=f"C4+{arguments.decision.upper()}", world_build_dir=arguments.world_build,
                               system_one_provider=arguments.provider, system_one_profile="relaxed"))
        raw, flagged, models, unavailable, outcomes = {}, {}, set(), 0, {}
        receipts = [json.loads(line) for line in (result.out_dir / "receipts.jsonl").read_text().splitlines()]
        traces = [json.loads(line) for line in (result.out_dir / "traces.jsonl").read_text().splitlines()]
        for case_id, receipt, trace in zip(result.manifest["cases"], receipts, traces):
            for call in trace.get("model_calls") or []:
                outcomes[call.get("reason") or "ok"] = outcomes.get(call.get("reason") or "ok", 0) + 1
            for decision in receipt["decisions"]:
                value = decision.get("value")
                if value is None and str(decision.get("target", "")).startswith(arguments.decision):
                    unavailable += 1
                if not value or not str(value.get("item", "")).startswith(f"{arguments.decision}:"):
                    continue
                key = (case_id, value["item"].split(":", 1)[1])
                if value.get("p_raw") is not None:
                    raw[key] = value["p_raw"]
                    flagged[key] = bool(value.get("rule_flagged"))
                    models.add(decision.get("model_version"))
        labels = labels_from_run(arguments.decision, result.out_dir, arguments.cases)
    keys = sorted(k for k in raw if k in labels)
    pairs = [(raw[k], labels[k]) for k in keys]
    report = {
        "provider": arguments.provider, "decision": arguments.decision, "template": arguments.template,
        "models": sorted(map(str, models)), "cases": str(arguments.cases.relative_to(ROOT)),
        "answered": len(raw), "labelled": len(keys), "unavailable_items": unavailable, "model_call_outcomes": outcomes,
        "campaign": campaign.summary(), "ceilings": {"calls": arguments.max_calls, "input_tokens": arguments.max_input_tokens},
        "all": summary(pairs),
        "rule_flagged": summary([(raw[k], labels[k]) for k in keys if flagged.get(k)]),
        "candidates": summary([(raw[k], labels[k]) for k in keys if not flagged.get(k)]),
        "nested_cv": nested_band_check(keys, raw, labels, flagged, arguments.tolerance) if any(labels[k] for k in keys) else None,
        "tolerance": arguments.tolerance, "git_commit": git_state()["git_commit"],
    }
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("template", "answered", "labelled", "campaign", "all", "rule_flagged", "candidates", "nested_cv")}))
