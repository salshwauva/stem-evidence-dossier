"""Typed records for a query, a comparison, a stance and a search result.

The records follow plan sections 34, 37 and 39. They are frozen and they reject
unknown fields, like every record in the core model.
"""

from collections.abc import Mapping
from enum import StrEnum

from evidence_dossier.model import (
    ClaimType,
    ComparabilityLevel,
    Domain,
    EvidenceSpan,
    FrozenModel,
    Measurement,
    Result,
    ResultDirection,
    SourceLevel,
    Stance,
    Term,
)


class Relationship(StrEnum):
    """The relation that a query states between its subject and its measurement.

    The three values are the relations that the deterministic parser reads from
    text (plan section 34). A caller may build a proposition with any of them.
    """

    INCREASES = "INCREASES"
    REDUCES = "REDUCES"
    IMPROVES = "IMPROVES"


# The direction that each relation expects of a result.
EXPECTED_DIRECTIONS: Mapping[Relationship, ResultDirection] = {
    Relationship.INCREASES: ResultDirection.INCREASED,
    Relationship.REDUCES: ResultDirection.DECREASED,
    Relationship.IMPROVES: ResultDirection.IMPROVED,
}


class QueryProposition(FrozenModel):
    """One user proposition in typed form (plan section 34).

    The parser fills subject, relationship and measurement from the text. It
    leaves method, comparator, context and domain empty when the text does not
    state them, and it names the empty ones in unresolved_fields.
    """

    original_text: str
    domain: Domain | None = None
    subject: Term
    relationship: Relationship
    measurement: Term
    method: Term | None = None
    comparator: Term | None = None
    context: str | None = None
    expected_direction: ResultDirection
    parser_version: str
    # The fields that the text did not state, such as "comparator" or "context".
    unresolved_fields: tuple[str, ...] = ()


class EvidenceFilters(FrozenModel):
    """Structured filters that narrow retrieval before ranking (plan section 36)."""

    domain: Domain | None = None
    claim_type: ClaimType | None = None
    source_levels: tuple[SourceLevel, ...] = ()
    result_directions: tuple[ResultDirection, ...] = ()
    research_work_id: str | None = None
    study_id: str | None = None


class DimensionComparison(FrozenModel):
    """One comparability dimension with the level it reached and the reason (plan section 37).

    missing_fact separates a fact that the claim never states from a value that
    the claim states and that does not match the query.
    """

    dimension: str
    level: ComparabilityLevel
    missing_fact: bool = False
    reason: str


class ComparabilityAssessment(FrozenModel):
    """How closely one claim matches one proposition (plan sections 37 and 38)."""

    level: ComparabilityLevel
    dimensions: tuple[DimensionComparison, ...]
    # The dimensions that the domain profile names (plan section 38).
    profile_features: tuple[str, ...]
    # True when the claim measures an accepted proxy instead of the asked measurement.
    proxy_measurement: bool = False
    rules_version: str

    def dimension(self, name: str) -> DimensionComparison | None:
        """Return the comparison for one dimension, or None when it has none."""
        for comparison in self.dimensions:
            if comparison.dimension == name:
                return comparison
        return None


class StanceAssessment(FrozenModel):
    """How one claim relates to one proposition, with the rule that decided it.

    Plan section 39 lists the fields and it forbids a model confidence score.
    """

    query_id: str
    claim_id: str
    stance: Stance
    comparability: ComparabilityAssessment
    reason: str
    rules_version: str


class EvidenceHit(FrozenModel):
    """One retrieved claim with its stance and its full provenance."""

    claim_id: str
    research_work_id: str
    study_id: str
    source_level: SourceLevel
    claim_type: ClaimType
    claim_text: str
    subject: Term
    measurement: Measurement | None
    result: Result
    stance: Stance
    reason: str
    comparability: ComparabilityAssessment
    evidence_span: EvidenceSpan


class EvidenceSearchResult(FrozenModel):
    """The organized answer to one search: the query, the hits and the stance groups."""

    query_id: str
    query: QueryProposition
    hits: tuple[EvidenceHit, ...]
    # Claim IDs per stance, so a caller reads the groups without a second pass.
    stance_groups: Mapping[Stance, tuple[str, ...]]
    total_candidates: int
    limit: int
    offset: int
    ranking_version: str
