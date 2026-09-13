"""The shape that every domain profile shares (plan section 23)."""

from dataclasses import dataclass

from evidence_dossier.model import (
    BiologyAttributes,
    ChemistryAttributes,
    ComputerScienceAttributes,
    Domain,
    EngineeringAttributes,
    PhysicsAttributes,
)

type AttributeModel = (
    type[BiologyAttributes]
    | type[ComputerScienceAttributes]
    | type[ChemistryAttributes]
    | type[PhysicsAttributes]
    | type[EngineeringAttributes]
)

# Generic evidence gap dimensions (plan section 43).
GENERIC_EVIDENCE_GAP_DIMENSIONS: tuple[str, ...] = (
    "independent replication",
    "diverse contexts",
    "direct measurements",
    "alternative methods",
    "external validation",
)

# Generic comparability dimensions (plan section 37).
GENERIC_COMPARABILITY_DIMENSIONS: tuple[str, ...] = (
    "subject",
    "method",
    "context",
    "comparator",
    "measurement",
    "conditions",
    "evidence directness",
)


@dataclass(frozen=True)
class DomainProfile:
    """Plain data that one domain adds on top of the generic core (plan section 23).

    The generic schema stays authoritative, and a profile only enriches it
    (plan section 28). Normalization rules belong to the extraction branch.
    """

    domain: Domain
    # The attribute class that this profile adds to contexts, methods and comparators.
    attribute_model: AttributeModel | None
    expected_entities: tuple[str, ...]
    common_methods: tuple[str, ...]
    common_measurement_types: tuple[str, ...]
    evidence_gap_dimensions: tuple[str, ...]
    # Conditions that decide whether two claims are comparable (plan sections 37 and 38).
    comparability_features: tuple[str, ...]
