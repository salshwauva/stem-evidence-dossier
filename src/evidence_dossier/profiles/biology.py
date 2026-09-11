"""The biology profile."""

from dataclasses import dataclass

from evidence_dossier.model import BiologyAttributes, Domain
from evidence_dossier.profiles.base import (
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)


@dataclass(frozen=True)
class BiologyProfile(DomainProfile):
    """Biology profile. The values come from plan sections 18, 20, 24 and 38."""

    domain: Domain = Domain.BIOLOGY
    attribute_model: AttributeModel | None = BiologyAttributes
    expected_entities: tuple[str, ...] = (
        "target",
        "organism",
        "cell line",
        "tissue",
        "disease model",
        "intervention",
        "dose",
        "duration",
        "assay",
    )
    common_methods: tuple[str, ...] = (
        "knockdown",
        "gene editing",
        "drug treatment",
        "assay protocol",
    )
    common_measurement_types: tuple[str, ...] = ("cell viability", "protein abundance")
    # Plan section 43 names no biology additions, so the generic dimensions apply.
    evidence_gap_dimensions: tuple[str, ...] = GENERIC_EVIDENCE_GAP_DIMENSIONS
    comparability_features: tuple[str, ...] = (
        "target",
        "intervention",
        "organism",
        "model",
        "endpoint",
        "dose context",
    )
