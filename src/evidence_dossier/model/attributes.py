"""Typed attributes that a domain profile adds to a context, a method or a comparator.

The union is closed. A new domain profile adds its attribute class to this
module and to DomainAttributes, so model keeps no imports from profiles
(ADR 0001 and ADR 0003).
"""

from typing import Annotated, Literal

from pydantic import Field

from evidence_dossier.model.base import FrozenModel


class BiologyAttributes(FrozenModel):
    """Biology attributes from plan section 24. They stay out of the generic core."""

    profile: Literal["biology"] = "biology"
    organism: str | None = None
    cell_line: str | None = None
    tissue: str | None = None
    disease_model: str | None = None
    intervention: str | None = None
    dose: str | None = None
    duration: str | None = None
    assay: str | None = None


class ComputerScienceAttributes(FrozenModel):
    """Computer science attributes from plan section 25.

    Some names repeat generic ResearchContext fields because section 25 lists
    them. The generic field stays authoritative (plan section 28).
    """

    profile: Literal["computer_science"] = "computer_science"
    task: str | None = None
    algorithm: str | None = None
    model: str | None = None
    model_version: str | None = None
    dataset: str | None = None
    benchmark: str | None = None
    training_data: str | None = None
    hardware: str | None = None
    baseline: str | None = None
    hyperparameters: str | None = None
    evaluation_metric: str | None = None
    compute_budget: str | None = None


class ChemistryAttributes(FrozenModel):
    """Chemistry attributes from plan section 27. Values keep the text the paper used."""

    profile: Literal["chemistry"] = "chemistry"
    compound: str | None = None
    catalyst: str | None = None
    solvent: str | None = None
    temperature: str | None = None
    pressure: str | None = None
    concentration: str | None = None
    reaction_time: str | None = None
    yield_: str | None = Field(default=None, alias="yield")
    selectivity: str | None = None


class PhysicsAttributes(FrozenModel):
    """Physics attributes. Plan section 23 names a PhysicsProfile and lists no fields for it.

    The fields come from the physics parts of the plan: a measurement on a physical
    system (section 14), the context fields system, material, environment, simulation
    and theoretical_assumptions (section 17), the measurement examples temperature and
    pressure (section 20), and the microwave frequency in the physics query (section 4).
    ADR 0011 records the choice. apparatus holds the system, and sample holds the
    material, so neither name shadows the generic context field (plan section 28).

    theoretical_assumptions does repeat a generic ResearchContext name. The generic
    field lists the assumptions of the study as a tuple. Every attribute field is one
    optional string (ADR 0003), so this field holds the assumption that the claim
    rests on, in the words of the paper. The generic list stays authoritative for the
    study. The comparability engine reads a generic field only when it holds a string,
    so for this name it reads the physics field and never the generic tuple.
    """

    profile: Literal["physics"] = "physics"
    apparatus: str | None = None
    sample: str | None = None
    temperature: str | None = None
    pressure: str | None = None
    field_strength: str | None = None
    wavelength: str | None = None
    instrument: str | None = None
    simulation_code: str | None = None
    theoretical_assumptions: str | None = None


class EngineeringAttributes(FrozenModel):
    """Engineering attributes. Plan section 23 names an EngineeringProfile and lists no fields.

    The fields come from the engineering parts of the plan: the domain scope in
    section 3, the context fields system, material and environment in section 17,
    the tensile strength example in section 20, and the systems extension in section
    26, which lists hardware, workload, concurrency and network conditions. ADR 0011
    records the choice. system and material repeat generic ResearchContext fields, and
    the generic field stays authoritative (plan section 28).
    """

    profile: Literal["engineering"] = "engineering"
    system: str | None = None
    component: str | None = None
    material: str | None = None
    load: str | None = None
    operating_conditions: str | None = None
    standard: str | None = None
    test_method: str | None = None
    duty_cycle: str | None = None
    tolerance: str | None = None


# The profile tag picks the attribute class. An unknown tag fails validation.
DomainAttributes = Annotated[
    BiologyAttributes
    | ComputerScienceAttributes
    | ChemistryAttributes
    | PhysicsAttributes
    | EngineeringAttributes,
    Field(discriminator="profile"),
]
