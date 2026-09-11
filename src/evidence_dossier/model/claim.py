"""Evidence records: studies, claims and the parts that describe a claim (plan sections 14 to 22)."""

from pydantic import Field

from evidence_dossier.model.attributes import DomainAttributes
from evidence_dossier.model.base import FrozenModel
from evidence_dossier.model.document import Section
from evidence_dossier.model.enums import ClaimType, Domain, ResultDirection


class Term(FrozenModel):
    """A name as the source wrote it, next to the canonical form that normalization sets."""

    original: str
    canonical: str | None = None


class ResearchContext(FrozenModel):
    """What a study examined (plan section 17). Every field is domain neutral.

    Biology fields such as organism and cell line live on BiologyAttributes (ADR 0001).
    """

    domain: Domain
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


class Method(FrozenModel):
    """What the researchers did (plan section 18)."""

    name: Term
    method_type: str | None = None
    # Values keep the text the paper used, such as "3e-4" or "32".
    parameters: dict[str, str] = Field(default_factory=dict)
    domain_attributes: DomainAttributes | None = None


class Comparator(FrozenModel):
    """The baseline, control or reference that a claim compares against (plan section 19)."""

    name: Term
    comparator_type: str | None = None
    configuration: str | None = None
    domain_attributes: DomainAttributes | None = None


class Measurement(FrozenModel):
    """The quantity that a study measured (plan section 20)."""

    name: Term
    category: str | None = None
    measurement_method: str | None = None
    unit: Term | None = None


class Result(FrozenModel):
    """The reported outcome of a measurement (plan section 21)."""

    direction: ResultDirection
    value: float | None = None
    unit: Term | None = None
    effect_size: float | None = None
    uncertainty: str | None = None
    statistical_significance: bool | None = None
    # Text, because papers often report a bound such as "< 0.001".
    p_value: str | None = None
    confidence_interval: str | None = None
    result_text: str | None = None


class EvidenceSpan(FrozenModel):
    """The exact passage that a claim comes from (plan section 22).

    Offsets count Unicode code points in the section text, the unit that
    Python string slicing uses.
    """

    research_work_id: str
    section_id: str
    start_offset: int
    end_offset: int
    source_text: str

    def matches(self, section: Section) -> bool:
        """Return True when this span names the section and its offsets hold source_text.

        The check needs 0 <= start_offset < end_offset <= len(section.text). Python
        slicing clamps or wraps offsets outside that range, so the bounds come first.
        """
        return (
            self.section_id == section.id
            and 0 <= self.start_offset < self.end_offset <= len(section.text)
            and section.text[self.start_offset : self.end_offset] == self.source_text
        )


class Study(FrozenModel):
    """One coherent evaluation or analysis inside a research work (plan section 14)."""

    id: str
    research_work_id: str
    description: str


class EvidenceClaim(FrozenModel):
    """One claim from one study, with its context and its source passage (plan section 15)."""

    id: str
    research_work_id: str
    study_id: str
    # Links the claim to the extraction configuration that produced it (plan increment 3).
    extraction_run_id: str | None = None
    claim_type: ClaimType
    claim_text: str
    normalized_claim: str | None = None
    subject: Term
    predicate: str
    # The object of the predicate, such as "neuronal survival" (the plan's "object / outcome").
    outcome: str | None = None
    research_context: ResearchContext
    method: Method | None = None
    comparator: Comparator | None = None
    measurement: Measurement | None = None
    result: Result
    evidence_span: EvidenceSpan
