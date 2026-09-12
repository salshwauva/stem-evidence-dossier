from collections.abc import Iterator

import pytest

from evidence_dossier.model import (
    ComparabilityLevel,
    Domain,
    EvidenceClaim,
    Measurement,
    Result,
    ResultDirection,
    Stance,
    StanceAssessment,
    Term,
)
from evidence_dossier.profiles import get_profile
from evidence_dossier.query import (
    POLARITY_VERSION,
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
    # Review finding 2 changed this reason. The family sets are gone, so a plain
    # same direction pair now reads as a raw direction match.
    "claim-supports": (Stance.SUPPORTS, ComparabilityLevel.EXACT, "matches the expected"),
    "claim-contradicts": (Stance.CONTRADICTS, ComparabilityLevel.EXACT, "opposite"),
    "claim-mixed": (Stance.MIXED, ComparabilityLevel.EXACT, "mixed result"),
    # Review finding 1 changed this reason. The null branch now states the
    # significance flag in words instead of printing the flag value.
    "claim-null": (Stance.NULL, ComparabilityLevel.EXACT, "no significance reported"),
    "claim-indirect": (Stance.INDIRECT, ComparabilityLevel.HIGH, "evidence directness"),
    "claim-incomparable": (
        Stance.INSUFFICIENTLY_COMPARABLE,
        ComparabilityLevel.INCOMPATIBLE,
        "subject dimension",
    ),
}

# One proposition shape for the polarity cases: the expected direction stays
# DECREASED and only the measurement changes.
POLARITY_TEXT = (
    "retrieval-augmented generation reduces {measurement}"
    " compared with the same model without retrieval"
)


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


def _variant(claim: EvidenceClaim, **update: object) -> EvidenceClaim:
    return claim.model_copy(update=update)


def _classify(proposition_text: str, claim: EvidenceClaim) -> StanceAssessment:
    """Run the comparability engine and the classifier on one proposition and one claim."""
    proposition = parse_query(proposition_text, domain=Domain.COMPUTER_SCIENCE)
    assessment = ComparabilityEngine().assess(
        proposition, claim, get_profile(Domain.COMPUTER_SCIENCE)
    )
    return StanceClassifier().classify(proposition, claim, assessment)


def _reported_on(measurement: str, direction: ResultDirection) -> StanceAssessment:
    """Classify a claim that reports one direction on one measurement, expected DECREASED."""
    base, _ = stance_paper()
    claim = _variant(
        base.claim,
        id=f"claim-{measurement.replace(' ', '-')}",
        outcome=measurement,
        measurement=Measurement(name=Term(original=measurement)),
        result=Result(direction=direction, statistical_significance=True),
    )
    return _classify(POLARITY_TEXT.format(measurement=measurement), claim)


def _improved_on(measurement: str) -> StanceAssessment:
    return _reported_on(measurement, ResultDirection.IMPROVED)


@pytest.mark.parametrize("direction", [ResultDirection.UNCHANGED, ResultDirection.NOT_OBSERVED])
@pytest.mark.parametrize(
    ("significance", "wording"),
    [(True, "reported as significant"), (False, "no significance reported")],
)
def test_both_null_directions_are_null_at_either_significance(
    direction: ResultDirection, significance: bool, wording: str
) -> None:
    """Review finding 1: the flag picks the wording of the reason, never the stance."""
    base, _ = stance_paper()
    claim = _variant(
        base.claim,
        result=Result(direction=direction, statistical_significance=significance),
    )

    result = _classify(RAG_TEXT, claim)

    assert result.stance is Stance.NULL
    assert direction in result.reason
    assert wording in result.reason


def test_an_improvement_on_a_lower_is_better_measurement_supports() -> None:
    result = _improved_on("factual error rate")

    assert result.stance is Stance.SUPPORTS
    assert "LOWER_IS_BETTER" in result.reason


def test_an_improvement_on_a_higher_is_better_measurement_contradicts() -> None:
    """Review finding 2: an IMPROVED report no longer agrees with DECREASED by assumption."""
    result = _improved_on("accuracy")

    assert result.stance is Stance.CONTRADICTS
    assert "HIGHER_IS_BETTER" in result.reason


def test_an_improvement_on_an_unknown_measurement_is_indirect() -> None:
    result = _improved_on("widget sparkle")

    assert result.stance is Stance.INDIRECT
    assert "widget sparkle" in result.reason
    assert POLARITY_VERSION in result.reason


def test_the_suffix_rule_decides_a_measurement_the_table_does_not_list() -> None:
    result = _improved_on("refusal rate")

    assert result.stance is Stance.SUPPORTS
    assert "LOWER_IS_BETTER" in result.reason


def test_a_plain_same_direction_case_needs_no_polarity_table() -> None:
    """DECREASED against an expected DECREASED holds even for an unknown measurement."""
    base, _ = stance_paper()
    claim = _variant(
        base.claim,
        outcome="widget sparkle",
        measurement=Measurement(name=Term(original="widget sparkle")),
        result=Result(direction=ResultDirection.DECREASED, statistical_significance=True),
    )

    result = _classify(POLARITY_TEXT.format(measurement="widget sparkle"), claim)

    assert result.stance is Stance.SUPPORTS
    assert "matches the expected" in result.reason


def test_every_reason_names_the_polarity_table_version(store: Store) -> None:
    results = search_evidence(store, RAG_TEXT)

    assert all(POLARITY_VERSION in assessment.reason for assessment in results.assessments)


def test_a_worsening_on_a_lower_is_better_measurement_contradicts() -> None:
    """Review finding 2: WORSENED no longer shares a family with the expected DECREASED."""
    result = _reported_on("factual error rate", ResultDirection.WORSENED)

    assert result.stance is Stance.CONTRADICTS
    assert "INCREASED against DECREASED" in result.reason


def test_a_worsening_on_an_unknown_measurement_is_indirect() -> None:
    result = _reported_on("widget sparkle", ResultDirection.WORSENED)

    assert result.stance is Stance.INDIRECT
    assert "widget sparkle" in result.reason
    assert POLARITY_VERSION in result.reason


def test_a_worsening_on_a_higher_is_better_measurement_supports() -> None:
    result = _reported_on("accuracy", ResultDirection.WORSENED)

    assert result.stance is Stance.SUPPORTS
    assert "both as DECREASED" in result.reason
