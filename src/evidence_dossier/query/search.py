"""The query pipeline: parse, retrieve, assess, classify and organize (plan sections 35 and 45)."""

import uuid
from datetime import UTC, datetime

from evidence_dossier.model import (
    ComparabilityLevel,
    CorpusScope,
    Domain,
    Dossier,
    DossierCounts,
    EvidenceClaim,
    FrozenModel,
    QueryProposition,
    SourceLevel,
    Stance,
    StanceAssessment,
)
from evidence_dossier.profiles import get_profile
from evidence_dossier.query.comparability import ComparabilityEngine
from evidence_dossier.query.parser import parse_query
from evidence_dossier.query.retrieval import Candidate, Retriever
from evidence_dossier.query.stance import StanceClassifier
from evidence_dossier.store import Store

# The order in which results appear (plan section 6).
STANCE_ORDER: tuple[Stance, ...] = (
    Stance.SUPPORTS,
    Stance.CONTRADICTS,
    Stance.MIXED,
    Stance.NULL,
    Stance.INDIRECT,
    Stance.INSUFFICIENTLY_COMPARABLE,
)


class Provenance(FrozenModel):
    """Where a claim comes from, for the audit trail (plan section 22)."""

    research_work_id: str
    study_id: str
    section_id: str
    start_offset: int
    end_offset: int
    source_text: str


class EvidenceItem(FrozenModel):
    """One organized result: the claim, its stance, its comparability and the reasons."""

    claim: EvidenceClaim
    stance: Stance
    comparability: ComparabilityLevel
    comparability_reasons: tuple[str, ...]
    stance_reason: str
    provenance: Provenance


class StanceGroup(FrozenModel):
    stance: Stance
    items: tuple[EvidenceItem, ...]


class EvidenceResults(FrozenModel):
    """Organized results, next to the separate retrieval and stance records (plan section 53)."""

    proposition: QueryProposition
    candidates: tuple[Candidate, ...]
    assessments: tuple[StanceAssessment, ...]
    groups: tuple[StanceGroup, ...]


def search_evidence(
    store: Store,
    text: str,
    *,
    domain: Domain | None = None,
    source_level: SourceLevel | None = None,
    limit: int = 20,
    dataset: str | None = None,
    system: str | None = None,
    population: str | None = None,
) -> EvidenceResults:
    """Run the pipeline for a proposition text and store the proposition and its assessments."""
    proposition = parse_query(
        text, domain=domain, dataset=dataset, system=system, population=population
    )
    candidates = Retriever(store).retrieve(proposition, source_level=source_level, limit=limit)
    engine = ComparabilityEngine()
    classifier = StanceClassifier()
    items: list[EvidenceItem] = []
    assessments: list[StanceAssessment] = []
    store.add_query_proposition(proposition)
    for candidate in candidates:
        claim = candidate.claim
        comparability = engine.assess(
            proposition, claim, get_profile(claim.research_context.domain)
        )
        assessment = classifier.classify(proposition, claim, comparability)
        store.add_stance_assessment(assessment)
        assessments.append(assessment)
        span = claim.evidence_span
        items.append(
            EvidenceItem(
                claim=claim,
                stance=assessment.stance,
                comparability=comparability.level,
                comparability_reasons=comparability.reasons(),
                stance_reason=assessment.reason,
                provenance=Provenance(
                    research_work_id=claim.research_work_id,
                    study_id=claim.study_id,
                    section_id=span.section_id,
                    start_offset=span.start_offset,
                    end_offset=span.end_offset,
                    source_text=span.source_text,
                ),
            )
        )
    groups = tuple(
        StanceGroup(stance=stance, items=tuple(item for item in items if item.stance is stance))
        for stance in STANCE_ORDER
    )
    return EvidenceResults(
        proposition=proposition,
        candidates=tuple(candidates),
        assessments=tuple(assessments),
        groups=groups,
    )


def build_dossier(
    store: Store,
    text: str,
    *,
    domain: Domain | None = None,
    source_level: SourceLevel | None = None,
    limit: int = 20,
) -> tuple[Dossier, EvidenceResults]:
    """Search, then store a dossier with counts by stance and the corpus scope (plan section 45).

    The counts keep claims apart from studies and works, and no count is a
    probability that the proposition holds.
    """
    results = search_evidence(store, text, domain=domain, source_level=source_level, limit=limit)
    items = [item for group in results.groups for item in group.items]
    by_level = store.count_claims_by_source_level()
    dossier = Dossier(
        id=f"dossier_{uuid.uuid4().hex[:16]}",
        query_id=results.proposition.id,
        created_at=datetime.now(UTC),
        corpus_scope=CorpusScope(
            claim_count=sum(by_level.values()), source_levels=tuple(sorted(by_level))
        ),
        counts=DossierCounts(
            claims=len(items),
            studies=len({item.claim.study_id for item in items}),
            works=len({item.claim.research_work_id for item in items}),
            by_stance={group.stance: len(group.items) for group in results.groups},
        ),
    )
    store.add_dossier(dossier)
    return dossier, results
