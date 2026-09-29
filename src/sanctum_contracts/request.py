"""HLD v5.1 §12.0. Credentials are NOT request fields."""
from typing import Optional

from pydantic import Field, model_validator

from .base import Strict
from .enums import CallerProfile, Mode

SCHEMA_VERSION = "1.0"

_CREDENTIAL_HINTS = ("token", "credential", "password", "secret", "principal", "api_key")


class RetrieveRequest(Strict):
    schema_version: str = SCHEMA_VERSION
    request_id: str = Field(description="Opaque; must not encode case, family or answer")
    query: str
    mode: Mode
    scope: Optional[str] = Field(default=None, description="Can only narrow verified access")
    as_of: Optional[str] = None
    environment: Optional[str] = None
    budget_tokens: int = Field(gt=0)
    deadline_ms: int = Field(gt=0)
    caller_profile: CallerProfile = CallerProfile.agent

    @model_validator(mode="before")
    @classmethod
    def _no_credentials(cls, data):
        if isinstance(data, dict):
            for key in data:
                if key in cls.model_fields:
                    continue  # declared fields are fine (e.g. budget_tokens)
                if any(h in key.lower() for h in _CREDENTIAL_HINTS):
                    raise ValueError(
                        f"field {key!r} looks like a credential or principal; identity "
                        "comes from transport/session, not the request (HLD v5.1 §12.0)"
                    )
        return data
