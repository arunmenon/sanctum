from pydantic import BaseModel, ConfigDict


class Strict(BaseModel):
    """All wire models reject unknown fields and are immutable."""
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False,
                              protected_namespaces=())
