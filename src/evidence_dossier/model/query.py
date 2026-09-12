"""Query records: propositions, stance assessments and dossiers (plan sections 34, 39 and 45).

They live in model, not in query, because the store adds and gets them and
store imports nothing from query.
"""

from datetime import datetime

from pydantic import Field

from evidence_dossier.model.base import FrozenModel
from evidence_dossier.model.enums import (
    ComparabilityLevel,
    Domain,
    ResultDirection,
    SourceLevel,
    Stance,
)


class QueryProposition(FrozenModel):
    """A typed proposition parsed from a research question (plan section 34).

    A proposition does not need every field. parse_notes lists the parse rules
    that fired, so a reader can see how the text became these fields.
    """

    id: str
    text: str
    domain: Domain | None = None
    subject: str
    relationship: str
    measurement: str | None = None
    comparator: str | None = None
    expected_direction: ResultDirection | None = None
    # Optional context filters (plan section 48).
    dataset: str | None = None
    system: str | None = None
    population: str | None = None
    parse_notes: tuple[str, ...] = ()


class StanceAssessment(FrozenModel):
    """How one claim relates to one proposition, with the reason (plan section 39).

    The record holds no probability. The reason is a sentence, not a score.
    """

    query_id: str
    claim_id: str
    stance: Stance
    comparability: ComparabilityLevel
    reason: str
    created_at: datetime


class CorpusScope(FrozenModel):
    """What the store held when a dossier was built (plan section 45)."""

    claim_count: int
    source_levels: tuple[SourceLevel, ...] = ()


class DossierCounts(FrozenModel):
    """Counts at claim level, next to the distinct studies and works (plan section 45)."""

    claims: int
    studies: int
    works: int
    by_stance: dict[Stance, int] = Field(default_factory=dict)


class Dossier(FrozenModel):
    """A stored snapshot of the organized results for one proposition (plan section 45)."""

    id: str
    query_id: str
    created_at: datetime
    corpus_scope: CorpusScope
    counts: DossierCounts
