"""Shared configuration for every record in the core model."""

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Base for records that do not change after creation.

    Unknown fields fail validation. Pydantic would otherwise drop them without
    a trace, and the plan keeps invalid extractor output visible.
    """

    # The plan names fields such as model_version, and Pydantic 2.9 warns
    # about the model_ prefix unless the protected namespaces are empty.
    model_config = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())
