"""The fallback profile for every domain that has no profile of its own."""

from dataclasses import dataclass

from evidence_dossier.profiles.base import (
    GENERIC_COMPARABILITY_DIMENSIONS,
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)


@dataclass(frozen=True)
class GenericProfile(DomainProfile):
    """Fallback profile. It adds no attributes and uses the generic dimensions (plan sections 37 and 43)."""

    attribute_model: AttributeModel | None = None
    expected_entities: tuple[str, ...] = ()
    common_methods: tuple[str, ...] = ()
    common_measurement_types: tuple[str, ...] = ()
    evidence_gap_dimensions: tuple[str, ...] = GENERIC_EVIDENCE_GAP_DIMENSIONS
    comparability_features: tuple[str, ...] = GENERIC_COMPARABILITY_DIMENSIONS
