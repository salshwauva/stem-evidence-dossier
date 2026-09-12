from collections.abc import Iterator

import pytest

from evidence_dossier.model import ComparabilityLevel, Domain, Stance
from evidence_dossier.profiles import get_profile
from evidence_dossier.query import (
    STANCE_ORDER,
    ComparabilityEngine,
    StanceClassifier,
    parse_query,
    search_evidence,
)
from evidence_dossier.store import Store
from tests.query_corpus import seed, stance_paper
from tests.test_query_parser import RAG_TEXT

CASES: dict[str, tuple[Stance, ComparabilityLevel, str]] = {
    "claim-supports": (Stance.SUPPORTS, ComparabilityLevel.EXACT, "same direction family"),
    "claim-contradicts": (Stance.CONTRADICTS, ComparabilityLevel.EXACT, "opposite"),
    "claim-mixed": (Stance.MIXED, ComparabilityLevel.EXACT, "mixed result"),
    "claim-null": (Stance.NULL, ComparabilityLevel.EXACT, "statistical significance False"),
    "claim-indirect": (Stance.INDIRECT, ComparabilityLevel.HIGH, "evidence directness"),
    "claim-incomparable": (
        Stance.INSUFFICIENTLY_COMPARABLE,
        ComparabilityLevel.INCOMPATIBLE,
        "subject dimension",
    ),
}


@pytest.fixture
def store() -> Iterator[Store]:
    paper, claims = stance_paper()
    with Store(":memory:") as opened:
        seed(opened, [paper], claims)
        yield opened


@pytest.mark.parametrize("claim_id", list(CASES))
def test_each_stance_branch_gives_its_level_stance_and_reason(store: Store, claim_id: str) -> None:
    stance, level, deciding = CASES[claim_id]
    proposition = parse_query(RAG_TEXT, domain=Domain.COMPUTER_SCIENCE)
    claim = store.get_claim(claim_id)
    assert claim is not None

    assessment = ComparabilityEngine().assess(
        proposition, claim, get_profile(Domain.COMPUTER_SCIENCE)
    )
    result = StanceClassifier().classify(proposition, claim, assessment)

    assert assessment.level is level
    assert result.stance is stance
    assert result.comparability is level
    assert deciding in result.reason
    assert result.query_id == proposition.id
    assert result.claim_id == claim_id


def test_the_indirect_claim_fails_only_the_directness_dimension(store: Store) -> None:
    proposition = parse_query(RAG_TEXT)
    claim = store.get_claim("claim-indirect")
    assert claim is not None

    assessment = ComparabilityEngine().assess(
        proposition, claim, get_profile(Domain.COMPUTER_SCIENCE)
    )

    failed = [result.dimension for result in assessment.dimensions if not result.matched]
    assert failed == ["evidence directness"]
    assert "answer quality" in assessment.reasons()[-1]


def test_search_evidence_groups_results_in_the_plan_order_and_stores_them(store: Store) -> None:
    results = search_evidence(store, RAG_TEXT)

    assert [group.stance for group in results.groups] == list(STANCE_ORDER)
    assert {group.stance: [item.claim.id for item in group.items] for group in results.groups} == {
        Stance.SUPPORTS: ["claim-supports"],
        Stance.CONTRADICTS: ["claim-contradicts"],
        Stance.MIXED: ["claim-mixed"],
        Stance.NULL: ["claim-null"],
        Stance.INDIRECT: ["claim-indirect"],
        Stance.INSUFFICIENTLY_COMPARABLE: [],
    }
    assert len(results.candidates) == 5
    assert store.get_query_proposition(results.proposition.id) == results.proposition
    assert store.list_stance_assessments(results.proposition.id) == sorted(
        results.assessments, key=lambda assessment: assessment.claim_id
    )
