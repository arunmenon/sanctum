"""Fit a System One provider's D2 calibration on dev only (design page §8). Not run yet.

Labels: counterfactual, from scores only (never gold contents): a hub is useful for a dev case
when removing its manifest lowers the case's C1-fair recall (as tools/fit_d2_standin.py). Raw
answers: one live D2 round per dev case through `SystemOneClient` (the state mirrors the
broker's: query plus the pinned descriptors), capped by --max-calls, retries included.

Calibration and band selection are separated by cross-validation over case folds: Platt scaling
on logit(p_raw) is fitted on the training folds, and each held-out fold's calibrated predictions
are pooled to choose the bands (the largest skip band whose held-out harmful-skip rate stays
within --harm-tolerance; the use band is fixed at 0.7). The written file binds provider, resolved
model version, question template, descriptor release and decoding settings; a change to any of
them makes the SUT run shadow-only.

    PYTHONPATH=src:. python tools/fit_system_one.py --provider typesafe-jev --max-calls 120
"""
import argparse
import datetime
import json
import math
import os
import random
import shutil
import tempfile
from pathlib import Path

import yaml

from sanctum_ref.providers.http_systemone import TEMPLATE_VERSION, d2_questions
from sanctum_ref.providers import d2_request
from sanctum_run.gateway import released_hub_ids
from sanctum_run.runner import DEFAULT_HUBS_CONFIG, DEFAULT_WORLD_BUILD, git_state, load_cases, public_request
from sanctum_run.round3_state import STATE_V1
from sanctum_run.system_one_broker import STATE_KINDS, descriptor_release as release_of, load_descriptors, state_sources
from sanctum_systemone import CampaignBudget, SystemOneClient, load_provider_specs, set_campaign_budget
from tools.fit_d2_standin import recalls
from tools.measure_system_one_batches import dotenv

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "owners" / "manifests"
USE_BAND = 0.7


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def platt(points, steps=3000, rate=0.3):
    a, b = 1.0, 0.0
    for _ in range(steps):
        ga = gb = 0.0
        for x, y in points:
            p = 1 / (1 + math.exp(-(a * x + b)))
            ga += (p - y) * x
            gb += p - y
        a -= rate * ga / len(points)
        b -= rate * gb / len(points)
    return a, b


def brier(pairs) -> float:
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def ece(pairs, bins: int = 10) -> float:
    total = 0.0
    for index in range(bins):
        members = [(p, y) for p, y in pairs if index / bins <= p < (index + 1) / bins or (index == bins - 1 and p == 1.0)]
        if members:
            total += len(members) / len(pairs) * abs(sum(p for p, _ in members) / len(members)
                                                    - sum(y for _, y in members) / len(members))
    return total


def choose_skip_band(held_out, tolerance):
    """Largest skip band whose held-out harmful skips (useful sources skipped) stay within tolerance."""
    best = 0.0
    for band in [i / 100 for i in range(1, 50)]:
        skipped = [(p, y) for p, y in held_out if p < band]
        harmful = sum(y for _, y in skipped)
        if harmful <= tolerance * max(1, sum(y for _, y in held_out)):
            best = band
    return best


def broker_descriptors(include_held_back: bool = False) -> tuple[dict[str, str], str]:
    """Exactly the descriptor dict the runner's broker sends in state, and its release id."""
    descriptors = state_sources(load_descriptors(), released_hub_ids(DEFAULT_HUBS_CONFIG, include_held_back))
    return descriptors, release_of(descriptors)


def round3_release(state_kind) -> str:
    """The release the broker reports for a Round 3 state kind (it reports "none" for the v1 slices),
    so a binding names the exact state layout its answers were fitted on."""
    layout = STATE_KINDS.get(state_kind or "refs", STATE_V1)
    return "none" if layout == STATE_V1 else layout


def choose_use_band(held_out, max_false_rate):
    """Lowest use band (0.50 to 0.95) whose held-out promotions stay within the false-positive
    tolerance; 1.0 (never promote) when none does. Round 3 decisions only promote or add."""
    for band in [i / 100 for i in range(50, 96)]:
        promoted = [(p, y) for p, y in held_out if p >= band]
        if promoted and sum(1 - y for _, y in promoted) / len(promoted) <= max_false_rate:
            return band
    return 1.0


def round3_fit(arguments, spec, environment):
    """D6/D4: shadow-collect through the runner and broker, label on the evaluator side, fit."""
    from sanctum_eval.calibration_labels import labels_from_run
    from sanctum_run.process_sut import ProcessSUT
    from sanctum_run.runner import RunConfig, run
    decision = arguments.decision
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        (scratch / "no-calibration").mkdir()                     # shadow-only by construction
        sut_arguments = ["--config", "C4", "--round3", decision, "--round3-provider", arguments.provider,
                         "--calibration-dir", str(scratch / "no-calibration")]
        if arguments.template:
            sut_arguments += ["--round3-template", arguments.template]
        if arguments.memory_release:
            sut_arguments += ["--memory-release", arguments.memory_release]
        result = run(ProcessSUT(sut_arguments), RunConfig(
            cases_dir=arguments.cases, out_dir=scratch / "collect", seed=20260930, sut_name="ref",
            config_id=f"C4+{decision.upper()}", world_build_dir=arguments.world_build,
            system_one_provider=arguments.provider, system_one_profile="relaxed"))
        raw, models, usage, calls = {}, set(), {}, 0
        cases = result.manifest["cases"]
        receipts = [json.loads(line) for line in (result.out_dir / "receipts.jsonl").read_text().splitlines()]
        traces = [json.loads(line) for line in (result.out_dir / "traces.jsonl").read_text().splitlines()]
        for case_id, receipt, trace in zip(cases, receipts, traces):
            for call in trace.get("model_calls") or []:
                calls += call.get("calls", 0)
                for name, value in (call.get("usage") or {}).items():
                    if isinstance(value, (int, float)):
                        usage[name] = usage.get(name, 0) + value
            for decision_result in receipt["decisions"]:
                value = decision_result.get("value") or {}
                item = str(value.get("item", ""))
                if item.startswith(f"{decision}:") and value.get("p_raw") is not None:
                    raw[(case_id, item.split(":", 1)[1])] = value["p_raw"]
                    models.add(decision_result.get("model_version"))
        labels = labels_from_run(decision, result.out_dir, arguments.cases)
    if calls > arguments.max_calls:
        raise SystemExit(f"collect used {calls} calls, over the cap {arguments.max_calls}; nothing written")
    if len(models) != 1:
        raise SystemExit(f"resolved model not unique during collect: {sorted(map(str, models))}; nothing written")
    return raw, labels, models.pop(), usage, calls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "dev")
    parser.add_argument("--max-calls", type=int, default=120)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--harm-tolerance", type=float, default=0.05)
    parser.add_argument("--world-build", type=Path, default=DEFAULT_WORLD_BUILD)
    parser.add_argument("--decision", default="d2", choices=["d2", "d6", "d4"])
    parser.add_argument("--template", default=None, help="template id (configs/system_one_templates.yaml); default per decision")
    parser.add_argument("--max-input-tokens", type=int, default=200_000,
                        help="hard campaign ceiling, enforced before each HTTP attempt")
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument("--memory-release", default=None)
    parser.add_argument("--max-false-rate", type=float, default=0.2,
                        help="Round 3: tolerated share of false positives among held-out promotions")
    parser.add_argument("--model-revision", default=None,
                        help="checkpoint revision when the provider reports only a model family (Laya: /health revisions)")
    arguments = parser.parse_args()
    if "holdout" in str(arguments.cases.resolve()) or "acceptance" in str(arguments.cases.resolve()):
        raise SystemExit("fit on dev cases only")
    # hard campaign ceiling, enforced before every HTTP attempt in this process (the runner's broker
    # included); retries count; usage is recorded once per exchange
    campaign = CampaignBudget(arguments.max_calls, arguments.max_input_tokens, arguments.max_output_tokens)
    set_campaign_budget(campaign)
    spec = load_provider_specs(ROOT / "configs" / "system_one_providers.yaml")[arguments.provider]
    environment = {**dotenv(), **os.environ}
    if arguments.decision != "d2":
        raw, labels, model, usage, calls = round3_fit(arguments, spec, environment)
        keys = sorted(key for key in raw if key in labels)
        if not keys or not any(labels[k] for k in keys):
            raise SystemExit(f"{arguments.decision}: no labelled positives in the collect run; nothing written")
        case_ids = sorted({case_id for case_id, _ in keys})
        random.Random(20260930).shuffle(case_ids)
        folds = [set(case_ids[i::arguments.folds]) for i in range(arguments.folds)]
        held_out, raw_held_out = [], []
        for fold in folds:
            train = [(logit(raw[k]), labels[k]) for k in keys if k[0] not in fold]
            if not train:
                continue
            a, b = platt(train)
            held_out += [(1 / (1 + math.exp(-(a * logit(raw[k]) + b))), labels[k]) for k in keys if k[0] in fold]
            raw_held_out += [(raw[k], labels[k]) for k in keys if k[0] in fold]
        use = choose_use_band(held_out, arguments.max_false_rate)
        a, b = platt([(logit(raw[k]), labels[k]) for k in keys])
        from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
        template = TemplateRegistry(DEFAULT_TEMPLATES).resolve(arguments.decision, arguments.provider, arguments.template)
        if template.diagnostic:
            raise SystemExit(f"{template.id} is a diagnostic template: it is never calibrated into bands")
        out = ROOT / "configs" / "calibration" / f"{arguments.provider}@{model}.{arguments.decision}.yaml"
        if use >= 1.0:
            # no band met the tolerance: record the fit, but leave no live binding, so the SUT runs
            # shadow-only by absence of a calibration (never by a sentinel band)
            out = ROOT / "configs" / "calibration" / "rejected" / out.name
            out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml.safe_dump({
            "binding": {"provider": arguments.provider, "model": model, "model_revision": arguments.model_revision,
                        "decision": arguments.decision, "template": template.id,
                        "descriptor_release": round3_release(template.state), "decoding": "provider default"},
            "platt": {"a": round(a, 4), "b": round(b, 4)},
            "bands": {"use": use, "skip": 0.0},
            "provenance": {"fitted_on": "dev", "cases": len(case_ids), "points": len(keys),
                           "positives": sum(labels[k] for k in keys), "folds": arguments.folds,
                           "max_false_rate": arguments.max_false_rate, "http_calls": calls, "usage": usage,
                           "held_out": {"brier_calibrated": round(brier(held_out), 4), "ece_calibrated": round(ece(held_out), 4),
                                        "brier_raw": round(brier(raw_held_out), 4), "ece_raw": round(ece(raw_held_out), 4),
                                        "promoted_at_band": sum(1 for p, _ in held_out if p >= use),
                                        "false_promotions_at_band": sum(1 - y for p, y in held_out if p >= use)},
                           "label": f"sanctum_eval.calibration_labels ({arguments.decision})",
                           "fitted_at": datetime.date.today().isoformat(), "git_commit": git_state()["git_commit"]},
        }, sort_keys=False), encoding="utf-8")
        print(f"wrote {out}: platt a={a:.3f} b={b:.3f}, use band {use}, {len(keys)} points, {calls} calls, usage {usage}")
        print(f"held-out Brier {brier(held_out):.4f} (raw {brier(raw_held_out):.4f}), ECE {ece(held_out):.4f} (raw {ece(raw_held_out):.4f})")
        raise SystemExit(0)
    descriptors, descriptor_release = broker_descriptors()
    client = SystemOneClient(spec, spec.resolved_base_url(environment) or "https://api.typesafe.ai",
                             spec.requested_model(environment),
                             api_key=environment.get(spec.api_key_env) if spec.api_key_env else None)
    cases = {gold.case_id: public_request(gold).query for gold in load_cases(arguments.cases)}
    raw, calls, usage, models = {}, 0, {}, set()
    for case_id, query in cases.items():
        if calls + 2 > arguments.max_calls:
            raise SystemExit(f"spend cap reached after {calls} calls; nothing written")
        requests = [d2_request(hub, query, 60000) for hub in descriptors]
        outcome = client.decide({"query": query, "sources": descriptors}, d2_questions(requests), 60.0, max_calls=2)
        calls += outcome.calls
        for name, value in (outcome.usage or {}).items():
            usage[name] = usage.get(name, 0) + value
        if outcome.unavailable_reason or not outcome.model:
            continue
        models.add(outcome.model)
        for hub in descriptors:
            answer = outcome.answers.get(f"d2:{hub}")
            if answer:
                raw[(case_id, hub)] = answer["noul"]
    if len(models) != 1:
        raise SystemExit(f"resolved model changed during the fit: {sorted(models)}; nothing written")
    model = models.pop()
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        full = recalls(arguments.cases, scratch / "full", MANIFESTS, arguments.world_build)
        labels = {}
        for hub in descriptors:
            registry = scratch / f"without-{hub}"
            shutil.copytree(MANIFESTS, registry)
            (registry / f"{hub}.yaml").unlink()
            without = recalls(arguments.cases, scratch / f"run-{hub}", registry, arguments.world_build)
            for case_id, recall in full.items():
                labels[(case_id, hub)] = int(without.get(case_id, recall) < recall - 1e-9)
    keys = sorted(key for key in raw if key in labels)
    case_ids = sorted({case_id for case_id, _ in keys})
    random.Random(20260930).shuffle(case_ids)
    folds = [set(case_ids[i::arguments.folds]) for i in range(arguments.folds)]
    held_out, raw_held_out = [], []
    for fold in folds:
        train = [(logit(raw[k]), labels[k]) for k in keys if k[0] not in fold]
        a, b = platt(train)
        held_out += [(1 / (1 + math.exp(-(a * logit(raw[k]) + b))), labels[k]) for k in keys if k[0] in fold]
        raw_held_out += [(raw[k], labels[k]) for k in keys if k[0] in fold]
    skip = choose_skip_band(held_out, arguments.harm_tolerance)
    a, b = platt([(logit(raw[k]), labels[k]) for k in keys])
    out = ROOT / "configs" / "calibration" / f"{arguments.provider}@{model}.yaml"
    # The SUT finds a calibration by <provider>@<resolved model>. When a provider reports only a
    # model family (Laya: "laya-rl-agent"), the checkpoint revision is recorded in the binding and
    # is pinned by the running server, not verified per call: refit after any checkpoint change.
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({
        "binding": {"provider": arguments.provider, "model": model, "model_revision": arguments.model_revision,
                    "template": TEMPLATE_VERSION,
                    "descriptor_release": descriptor_release, "decoding": "provider default"},
        "platt": {"a": round(a, 4), "b": round(b, 4)},
        "bands": {"use": USE_BAND, "skip": skip},
        "provenance": {"fitted_on": "dev", "cases": len(case_ids), "points": len(keys),
                       "positives": sum(labels[k] for k in keys), "folds": arguments.folds,
                       "harm_tolerance": arguments.harm_tolerance, "http_calls": calls, "usage": usage,
                       "held_out": {"brier_calibrated": round(brier(held_out), 4), "ece_calibrated": round(ece(held_out), 4),
                                    "brier_raw": round(brier(raw_held_out), 4), "ece_raw": round(ece(raw_held_out), 4),
                                    "skipped_at_band": sum(1 for p, _ in held_out if p < skip),
                                    "harmful_skips_at_band": sum(y for p, y in held_out if p < skip)},
                       "label": "recall drop when the hub is removed (C1-fair runs)",
                       "fitted_at": datetime.date.today().isoformat(), "git_commit": git_state()["git_commit"]},
    }, sort_keys=False), encoding="utf-8")
    print(f"wrote {out}: platt a={a:.3f} b={b:.3f}, skip band {skip}, {calls} calls, usage {usage}")
    print(f"held-out Brier {brier(held_out):.4f} (raw {brier(raw_held_out):.4f}), ECE {ece(held_out):.4f} (raw {ece(raw_held_out):.4f})")
