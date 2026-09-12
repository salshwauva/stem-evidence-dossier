"""Boundary models for extractor output (plan sections 15 to 22 and 52).

The models mirror EvidenceClaim with the differences that the model output
needs: a study_key that the model chooses, plain strings where the core uses
Term (normalization adds the canonical value), and an evidence object with
only section_id and source_text (the pipeline computes the offsets). Each
claim carries its own method, comparator, measurement and result, and no
field holds a list of values (plan section 32). Unknown fields fail
validation.
"""

from pydantic import Field

from evidence_dossier.model import ClaimType, DomainAttributes, FrozenModel, ResultDirection


class CandidateStudy(FrozenModel):
    """One study, named by a key that the claims of the same output reference."""

    key: str = Field(min_length=1)
    description: str


class CandidateEvidence(FrozenModel):
    """The section and the exact passage that a claim comes from."""

    section_id: str
    source_text: str = Field(min_length=1)


class CandidateContext(FrozenModel):
    """ResearchContext without the domain, which the pipeline takes from the work."""

    system: str | None = None
    population: str | None = None
    dataset: str | None = None
    benchmark: str | None = None
    material: str | None = None
    environment: str | None = None
    hardware: str | None = None
    software: str | None = None
    model: str | None = None
    simulation: str | None = None
    theoretical_assumptions: tuple[str, ...] = ()
    domain_attributes: DomainAttributes | None = None


class CandidateMethod(FrozenModel):
    name: str = Field(min_length=1)
    method_type: str | None = None
    parameters: dict[str, str] = Field(default_factory=dict)
    domain_attributes: DomainAttributes | None = None


class CandidateComparator(FrozenModel):
    name: str = Field(min_length=1)
    comparator_type: str | None = None
    configuration: str | None = None
    domain_attributes: DomainAttributes | None = None


class CandidateMeasurement(FrozenModel):
    name: str = Field(min_length=1)
    category: str | None = None
    measurement_method: str | None = None
    unit: str | None = None


class CandidateResult(FrozenModel):
    direction: ResultDirection
    value: float | None = None
    unit: str | None = None
    effect_size: float | None = None
    uncertainty: str | None = None
    statistical_significance: bool | None = None
    p_value: str | None = None
    confidence_interval: str | None = None
    result_text: str | None = None


class CandidateClaim(FrozenModel):
    """One claim as the model reports it, before relationship validation."""

    study_key: str = Field(min_length=1)
    claim_type: ClaimType
    claim_text: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    outcome: str | None = None
    research_context: CandidateContext = CandidateContext()
    method: CandidateMethod | None = None
    comparator: CandidateComparator | None = None
    measurement: CandidateMeasurement | None = None
    result: CandidateResult
    evidence: CandidateEvidence


class CandidateClaims(FrozenModel):
    """The whole model output for one source document."""

    studies: tuple[CandidateStudy, ...]
    claims: tuple[CandidateClaim, ...]
