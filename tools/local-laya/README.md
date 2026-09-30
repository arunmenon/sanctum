# Local Laya CPU installation

Installed Laya 0.3.22 in `../.laya-venv` (Python 3.12.7), independently of the lab environment. Exact installed dependencies are in `requirements-installed.txt`.

Start with `./start-cpu.sh`. It binds only 127.0.0.1:8888, forces CPU, and preloads English. No hosted Jev key is required. Model weights are cached in the user's Hugging Face cache.

Verified `/health`: English checkpoint revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, actual device CPU, no fallback. The runtime reports `laya-rl-agent` in decision responses; record the checkpoint revision separately for reproducibility.

The lab's live Laya conformance test initially failed because the provider config declared no usage reporting. The installed runtime returns usage, so `laya-local.capabilities.reports_usage` was corrected to true.

This installation is not a calibrated routing benchmark. A 6000-character cap does not guarantee a token-budget fit; inspect truncation metadata. Startup warns that an out-of-range choice temperature for 11+ options was clamped, so affected confidence must be treated as uncalibrated. No calibrated keep/skip thresholds were fitted during installation.
