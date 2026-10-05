# Running and recovering experiments

Use this page after the [offline tutorial](quickstart.md). Commands run from repository root with Python 3.12. Paths below beginning `build/` are local inputs, not files included in a checkout.

## Choose the operation you need

| Goal | Use |
|---|---|
| Try a checkout without model calls | The [quickstart](quickstart.md) shipping example |
| Start or resume real agent attempts | Plan and dispatch below |
| Inspect progress or evaluate saved answers | Inspect and score below |
| Diagnose a stop or mismatched input | Recovery table below |

“Dispatch” means starting an actual attempt. A frozen schedule records which attempts are intended; it does not start them.

## Plan and dispatch

For any complete bundle, validate and freeze a schedule before running it:

```bash
PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py examples/agent-bundles/shipping/experiment.yaml
PYTHONPATH=src:. .venv/bin/python tools/plan_agent_run.py examples/agent-bundles/shipping/experiment.yaml --out build/my-fixture-run
PYTHONPATH=src:. .venv/bin/python tools/run_agent_attempt.py examples/agent-bundles/shipping/experiment.yaml --out build/my-fixture-run --task-id shipping-eligibility --arm direct --fixture
```

### Before a real Claude run

You need:

- An accepted bundle with reviewed questions and private criteria.
- An exact model and effort setting.
- An explicit inference budget and spend ledger.
- Verification that the installed CLI is isolated and respects round limits.
- A snapshot of the intended caller identity.
- The matching verified CLI binary on `PATH`.

The Sanctum setup also needs:

- A reviewed routing-memory release.
- Verified System One settings and matching runtime files.

The shipping fixture is intentionally not configured for model dispatch. It cannot start a real Claude run.

```bash
PYTHONPATH=src:. .venv/bin/python tools/run_agent_campaign.py /path/to/accepted-bundle/experiment.yaml --out build/my-native-run
```

That command invokes inference. Authenticate in the mode declared by the bundle. The helper reads first-party cached OAuth for subscription mode, or the API key for API mode; keys never go in argv or bundle files. The campaign records every terminal outcome and stops on unresolved dispatch, missing usage or provider/auth limits.

Restarting a campaign with unchanged inputs skips terminal attempts and dispatches never-started items. An unresolved `dispatched` row requires reconciliation first; do not delete it or silently replace its outcome. Changed config/corpus/proof hashes require a newly validated experiment, not editing frozen receipts.

## Inspect and score saved answers

Read `campaign-progress.json`, `campaign-result.json`, `attempts.json` and per-attempt `result.json`. For quality-driver progress, inspect `progress.json`, `stopped.json`, `calibration.json` and `complete.json` in its output directory. A historical stop marker is not by itself proof that a resumed process is stopped; inspect current process and timestamps.

The following scorer command creates a packet without inference. Replace the paths and task ID with one saved attempt from your bundle:

```bash
PYTHONPATH=src:. .venv/bin/python tools/score_agent_answer.py /path/to/bundle/experiment.yaml --task-id TASK_ID --attempt /path/to/result.json --answer /path/to/answer.json --quality-policy /path/to/evaluation-policy.json --judge-packet --out build/judge-packet.json
```

Supply `--review /path/to/review.json` instead of `--judge-packet` to derive a score from an existing semantic review. Without that review, semantic quality remains pending. `--human-acceptance` also needs the bundle's pinned human-reviewer registry.

```bash
PYTHONPATH=src:. .venv/bin/python tools/report_agent_run.py /path/to/bundle/experiment.yaml --run build/my-native-run --scores /path/to/scores.json --quality-policy /path/to/evaluation-policy.json
```

Reporting invokes no inference, but it validates the experiment and installed-CLI pins. It writes `comparison-report.json` under the run. The score map is keyed by scheduled attempt ID; semantic entries link to saved reviews within that run.

### Not portable yet: semantic evaluation driver

`tools/run_quality_evaluation.py` is a local reference driver, not a turnkey CLI for another machine. It invokes Sonnet to judge saved answers.

- It pins a developer-local Claude 2.1.288 binary.
- It reads cached subscription login, with a macOS Keychain fallback.
- It imports calibration fixtures and expects the current policy format.
- Reusing it requires selecting and verifying your own binary in a new pinned evaluation.

Do not copy personal paths into a general bundle or change an active evaluator mid-run. [Scoring](scoring.md) explains calibration and acceptance checks.

## Recovery table

| Symptom | Inspect | Safe next action |
|---|---|---|
| Missing PDLC authoring/corpus inputs | Candidate paths named by preparation tools | Use the checked-in fixture, or obtain/rebuild audited inputs; they are not recovered by git checkout |
| Corpus/runtime/CLI hash mismatch | Manifest, runtime pins and installed-CLI proofs | Reconcile the change; create new verification/config pins and a new experiment |
| Unknown live dispatch | `attempts.json`, native events and process state | Reconcile actual execution; preserve record, do not replay automatically |
| Unknown usage | Result/broker receipts and spend ledger | Reconcile provider usage; do not record unknown cost as zero |
| Auth or usage limit | Dispatch log and native terminal event | Restore declared authentication/capacity, then resume only undispatched items |
| Invalid judge schema | Original native reply, invalid review and retry receipt | One declared format retry; if still invalid, retain an unscored review failure and continue independent judgments |
| Changed judge packet/evaluator policy | Quality schedule hashes and saved packet | New evaluation version; preserve prior valid scores only with matching inputs and derivation |
| Protocol-invalid agent answer | Original `answer.json` | Retain zero-credit failure; no selective agent rerun |

Next: [agent harness](agent-harness.md), [scoring](scoring.md), [extending](extending.md).

[Back to start](README.md).
