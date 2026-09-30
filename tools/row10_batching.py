"""Prompt campaign row 10: order, context, single versus batched, identical repeats (D2, frozen subset).

Direct calls with the broker's D2 state shape on a fixed subset of dev cases (the first N case ids),
so the variants differ only in the property under test:
  sorted / reversed question order (one batched call per case), an identical repeat of the sorted
  request, a longer context (descriptors v2) with the same questions, and single-question calls
  (one call per source) on the first M cases. Reports paired probability changes, AUC against the
  counterfactual labels where both classes exist, truncation and usage. Campaign ceiling enforced
  before every HTTP attempt; the row is written to the campaign ledger.
"""
import argparse
import json
import os
import statistics
from pathlib import Path

import yaml

from sanctum_ref.providers import d2_request
from sanctum_ref.providers.http_systemone import d2_questions
from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
from sanctum_run.gateway import released_hub_ids
from sanctum_run.runner import DEFAULT_HUBS_CONFIG, git_state, load_cases, public_request
from sanctum_run.system_one_broker import state_sources
from sanctum_systemone import CampaignBudget, SystemOneClient, load_provider_specs, set_campaign_budget
from tools.ablate_system_one import record, remaining, roc_auc
from tools.measure_system_one_batches import dotenv

ROOT = Path(__file__).resolve().parents[1]


def descriptors(path: str) -> dict:
    return state_sources(yaml.safe_load((ROOT / path).read_text())["descriptors"], released_hub_ids(DEFAULT_HUBS_CONFIG))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "dev")
    parser.add_argument("--subset", type=int, default=5)
    parser.add_argument("--single-subset", type=int, default=3)
    parser.add_argument("--max-calls", type=int, required=True)
    parser.add_argument("--max-input-tokens", type=int, required=True)
    parser.add_argument("--labels", type=Path, required=True, help="cached D2 labels json from the ablation tool")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    left = remaining(arguments.provider)
    calls, tokens = arguments.max_calls, arguments.max_input_tokens
    if left is not None:
        calls, tokens = min(calls, left["calls"]), min(tokens, left["input_tokens"])
    campaign = CampaignBudget(calls, tokens, left["output_tokens"] if left else None)
    set_campaign_budget(campaign)
    spec = load_provider_specs(ROOT / "configs" / "system_one_providers.yaml")[arguments.provider]
    environment = {**dotenv(), **os.environ}
    client = SystemOneClient(spec, spec.resolved_base_url(environment) or "https://api.typesafe.ai",
                             spec.requested_model(environment),
                             api_key=environment.get(spec.api_key_env) if spec.api_key_env else None)
    template = TemplateRegistry(DEFAULT_TEMPLATES).resolve("d2", arguments.provider, "d2-noul-v1")
    short, long_ = descriptors("configs/d2_standin.yaml"), descriptors("configs/d2_descriptors_v2.yaml")
    labels = {tuple(key.split("\t")): value for key, value in json.loads(arguments.labels.read_text()).items()}
    golds = load_cases(arguments.cases)[:arguments.subset]
    batched = spec.capabilities.max_questions_per_call > 1
    results: dict[str, dict] = {}
    truncated = 0

    def ask(name, case_id, query, sources, order, per_call):
        nonlocal truncated
        requests = [d2_request(hub, query, 60000) for hub in order]
        questions = d2_questions(requests, template)
        if per_call == "single":
            answers = {}
            for qid, question in questions.items():
                outcome = client.decide({"query": query, "sources": sources}, {qid: question}, 60.0, max_calls=1)
                truncated += outcome.unavailable_reason == "truncated"
                answers.update(outcome.answers)
        else:
            outcome = client.decide({"query": query, "sources": sources}, questions, 60.0, max_calls=len(questions))
            truncated += outcome.unavailable_reason == "truncated"
            answers = outcome.answers
        for hub in order:
            answer = answers.get(f"d2:{hub}")
            if answer:
                results.setdefault(name, {})[(case_id, hub)] = answer["noul"]

    for index, gold in enumerate(golds):
        query = public_request(gold).query
        hubs = sorted(short)
        mode = "batch" if batched else "single"
        ask("sorted", gold.case_id, query, short, hubs, mode)
        ask("repeat", gold.case_id, query, short, hubs, mode)
        if batched:
            ask("reversed", gold.case_id, query, short, list(reversed(hubs)), mode)
        ask("long_context", gold.case_id, query, long_, hubs, mode)
        if batched and index < arguments.single_subset:
            ask("single", gold.case_id, query, short, hubs, "single")
    client.close()

    def paired(a, b):
        keys = sorted(set(results.get(a, {})) & set(results.get(b, {})))
        diffs = [abs(results[a][k] - results[b][k]) for k in keys]
        out = {"n": len(keys), "mean_abs_diff": round(statistics.mean(diffs), 4) if diffs else None,
               "max_abs_diff": round(max(diffs), 4) if diffs else None}
        for name in (a, b):
            pairs = [(results[name][k], labels[k]) for k in keys if k in labels]
            auc = roc_auc(pairs)
            out[f"auc_{name}"] = None if auc is None else round(auc, 4)
        out["labelled"] = sum(1 for k in keys if k in labels)
        out["positives"] = sum(labels[k] for k in keys if k in labels)
        return out

    report = {"provider": arguments.provider, "cases": [g.case_id for g in golds], "batched_provider": batched,
              "comparisons": {"sorted_vs_repeat": paired("sorted", "repeat"),
                              "sorted_vs_reversed": paired("sorted", "reversed"),
                              "short_vs_long_context": paired("sorted", "long_context"),
                              "batched_vs_single": paired("sorted", "single")},
              "truncated_calls": truncated, "campaign_row": campaign.summary(), "git_commit": git_state()["git_commit"]}
    record({"row": "10", "provider": arguments.provider, "template": "d2-noul-v1 (order/context/repeat)",
            "world_manifest": "n/a (direct D2 state)", **campaign.summary()})
    arguments.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report["comparisons"]), report["campaign_row"], "truncated", truncated)


if __name__ == "__main__":
    main()
