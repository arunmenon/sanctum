# Owner decisions blocking or shaping the lab

| ID | Decision | Proposed default | Blocks |
|---|---|---|---|
| D-GOAL | "Safe to build a real slice" or "evidence of superiority"? | Safe to build a real slice + directional evidence | M1 scope |
| D-GOLD | Who owns independent gold audits and the acceptance set? | Someone outside the sanctum-ref team | M1 exit; else results are "developer validation" |
| D-SCHEMA | Who approves the executable schema and reason-code list? | Sanctum platform lead | M0 exit |
| D-MARGIN | Non-inferiority margin and smallest useful gain | Set with the adopter | M5 |
| D-HYBRID | Hybrid DocHub required before H5 conclusions? | Yes, by M4 | M4 |
| D-ADAPTER | Real adapter survey (DI, Dobby, KaaS capabilities) | Run during M0–M1 | Hub capability realism |
| D-KESTREL | Use harvested Kestrel questions to shape families | Yes, at M1 | Question families |
| D-REF | Is sanctum-ref disposable or production seed? | Disposable reference | Code standards |
| D-EXT | External model use and spend | None before M6 | M6 |
| D-JEV | May hosted Jev see lab state? | Yes, synthetic lab data only; real data waits on data-class and egress approval (HLD Q6/Q13). Latency is measured per profile and is not a gate in the spike. See [System One providers](intelligence-layer/system-one-providers.md) | E1 (C3/C5 with Jev) |

## Working assumptions (adopted 2026-09-29 to unblock M1)

Proposed defaults above are adopted as working assumptions until an owner confirms or overrides them.

| ID | Assumption in force |
|---|---|
| D-GOAL | Safe to build a real slice + directional evidence |
| D-GOLD | Independent auditor TBD; until assigned, results are labelled "developer validation" |
| D-SCHEMA | M0 schema and reason codes treated as frozen; changes go through `export_schemas.py` diff review |
| D-REF | sanctum-ref is a disposable reference |
| D-EXT | No external model use before M6 |
