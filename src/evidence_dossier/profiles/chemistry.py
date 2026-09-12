"""The chemistry profile."""

from dataclasses import dataclass

from evidence_dossier.model import ChemistryAttributes, Domain
from evidence_dossier.profiles.base import (
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)


@dataclass(frozen=True)
class ChemistryProfile(DomainProfile):
    """Chemistry profile. The values come from plan sections 18, 20, 27 and 38."""

    domain: Domain = Domain.CHEMISTRY
    attribute_model: AttributeModel | None = ChemistryAttributes
    expected_entities: tuple[str, ...] = (
        "compound",
        "catalyst",
        "solvent",
        "temperature",
        "pressure",
        "concentration",
        "reaction time",
        "yield",
        "selectivity",
    )
    common_methods: tuple[str, ...] = (
        "reaction method",
        "catalyst",
        "synthesis procedure",
    )
    common_measurement_types: tuple[str, ...] = (
        "reaction yield",
        "selectivity",
        "temperature",
        "pressure",
    )
    # Plan section 43 names no chemistry additions, so the generic dimensions apply.
    evidence_gap_dimensions: tuple[str, ...] = GENERIC_EVIDENCE_GAP_DIMENSIONS
    comparability_features: tuple[str, ...] = (
        "reaction",
        "catalyst",
        "substrate",
        "conditions",
        "measurement",
    )
