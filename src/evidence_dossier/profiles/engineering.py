"""The engineering profile."""

from dataclasses import dataclass

from evidence_dossier.model import Domain, EngineeringAttributes
from evidence_dossier.profiles.base import (
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)


@dataclass(frozen=True)
class EngineeringProfile(DomainProfile):
    """Engineering profile. The values come from plan sections 3, 17, 18, 20, 26 and 38.

    Plan section 23 names the profile and lists no values for it, so each list
    below cites the section it reads. Ingestion gives this domain to the arXiv
    eess archive, which covers signal processing, image and video, audio and
    speech, and systems and control. ADR 0011 records the choice.
    """

    domain: Domain = Domain.ENGINEERING
    attribute_model: AttributeModel | None = EngineeringAttributes
    # The attribute fields (section 3 scope, section 17 context, section 26 systems).
    expected_entities: tuple[str, ...] = (
        "system",
        "component",
        "material",
        "load",
        "operating conditions",
        "standard",
        "test method",
        "duty cycle",
        "tolerance",
    )
    # Section 18 gives the shape of a method list. The entries cover the bench and
    # field work of section 3 and the eess subjects that reach this profile.
    common_methods: tuple[str, ...] = (
        "bench test",
        "field trial",
        "finite element simulation",
        "signal processing method",
        "control strategy",
    )
    # Section 20 names tensile strength and throughput. Section 26 names throughput
    # and energy. Each entry has a direction in the polarity table.
    common_measurement_types: tuple[str, ...] = (
        "tensile strength",
        "yield strength",
        "efficiency",
        "throughput",
        "cycle time",
    )
    # Plan section 43 names no engineering additions, so the generic dimensions apply.
    evidence_gap_dimensions: tuple[str, ...] = GENERIC_EVIDENCE_GAP_DIMENSIONS
    # Section 38 lists no engineering features and delegates the detail to the
    # profile. Two engineering results compare when they hold the same system and
    # component, under the same load and conditions, against the same standard.
    comparability_features: tuple[str, ...] = (
        "system",
        "component",
        "material",
        "load",
        "conditions",
        "standard",
        "hardware",
        "measurement",
    )
