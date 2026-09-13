"""The physics profile."""

from dataclasses import dataclass

from evidence_dossier.model import Domain, PhysicsAttributes
from evidence_dossier.profiles.base import (
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)


@dataclass(frozen=True)
class PhysicsProfile(DomainProfile):
    """Physics profile. Plan section 23 names the profile and lists no values for it.

    Each list below cites the plan section it comes from. ADR 0011 records the choice.
    """

    domain: Domain = Domain.PHYSICS
    attribute_model: AttributeModel | None = PhysicsAttributes
    # The attribute fields (section 17 context, section 20 measurements, section 4 query).
    expected_entities: tuple[str, ...] = (
        "system",
        "apparatus",
        "sample",
        "temperature",
        "pressure",
        "field strength",
        "wavelength",
        "instrument",
        "simulation code",
        "theoretical assumption",
    )
    # Section 14 calls a physics study a measurement on a physical system, and
    # section 17 names simulation and theoretical assumptions.
    common_methods: tuple[str, ...] = (
        "measurement",
        "spectroscopy",
        "scattering experiment",
        "numerical simulation",
        "analytical derivation",
    )
    # Section 20 names temperature and pressure. Section 4 asks about refractive index.
    common_measurement_types: tuple[str, ...] = (
        "temperature",
        "pressure",
        "refractive index",
    )
    # Plan section 43 names no physics additions, so the generic dimensions apply.
    evidence_gap_dimensions: tuple[str, ...] = GENERIC_EVIDENCE_GAP_DIMENSIONS
    # Section 38 lists no physics features and delegates the detail to the profile.
    # Two physics results compare when they hold the same system under the same
    # conditions, on the same apparatus and against the same assumptions.
    comparability_features: tuple[str, ...] = (
        "system",
        "sample",
        "apparatus",
        "conditions",
        "measurement",
        "theoretical assumptions",
    )
