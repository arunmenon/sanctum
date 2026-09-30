"""The `/v1/systemone` protocol core (docs/intelligence-layer/system-one-providers.md).

Neutral like `sanctum_contracts`: imports only the standard library, httpx and pydantic, so the
SUT's providers (`sanctum_ref.providers`) and the runner's broker (`sanctum_run`) share one
implementation of request building, batching, validation and the HTTP call."""
from .protocol import (  # noqa: F401
    CallOutcome, ProviderCapabilities, ProviderSpec, SystemOneClient, UnavailableReason,
    build_request, load_provider_specs, split_questions, truncation, validate_answers,
)
