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


# The profile tag picks the attribute class. An unknown tag fails validation.
DomainAttributes = Annotated[
    BiologyAttributes | ComputerScienceAttributes, Field(discriminator="profile")
]
