"""`python -m sanctum_hubs <hub> --build <build_dir>`: serve one hub over MCP stdio.

The token secret comes from the environment (`SANCTUM_LAB_TOKEN_SECRET`), never from argv.
An out-of-process hub verifies signature, audience and expiry; revocation is enforced where
hub tokens are minted (the token service refuses to exchange for revoked principals).
"""
import argparse
import os
import sys
from pathlib import Path

from .corpus import HUB_IDS, HubStore
from .interfaces import NoFailures
from .servers import build_hub_server

SECRET_ENVIRONMENT_VARIABLE = "SANCTUM_LAB_TOKEN_SECRET"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sanctum_hubs", description=__doc__)
    parser.add_argument("hub", choices=HUB_IDS)
    parser.add_argument("--build", type=Path, required=True, help="rendered build directory")
    parser.add_argument("--failure-profile", default="none")
    parser.add_argument("--failure-profiles", type=Path, default=None, help="failure_profiles.yaml")
    parser.add_argument("--seed", type=int, default=0, help="run seed for failure draws")
    parser.add_argument("--time-scale", type=float, default=None)
    arguments = parser.parse_args(argv)

    secret = os.environ.get(SECRET_ENVIRONMENT_VARIABLE)
    if not secret:
        print(f"{SECRET_ENVIRONMENT_VARIABLE} is not set", file=sys.stderr)
        return 2
    from .tokens import verifier_from_secret   # owned by the token service module
    store = HubStore.load(arguments.build / "hubs" / arguments.hub)
    if arguments.failure_profile == "none":
        failures = NoFailures()
    else:
        if arguments.failure_profiles is None:
            parser.error("--failure-profiles is required for a profile other than none")
        from .failure import load_failure_injector
        failures = load_failure_injector(arguments.failure_profiles, arguments.failure_profile,
                                         arguments.seed, arguments.time_scale)
    build_hub_server(store, verifier_from_secret(secret.encode("utf-8")), failures).run("stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
