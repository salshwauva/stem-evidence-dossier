"""Stance classifier: how a comparable claim relates to the proposition (plan section 39).

The classifier runs after the comparability engine and never changes the
candidate list. Every assessment carries a reason sentence and no probability.

Two rules follow the plan lists rather than the worked example in plan section 7.
UNCHANGED and NOT_OBSERVED are NULL, because plan section 39 lists NULL next to
CONTRADICTS and plan section 21 keeps the two directions apart from the opposite
ones.

The second rule reads the plan section 21 directions in two groups. INCREASED and
DECREASED are raw directions: they say which way the number moved. IMPROVED and
WORSENED are judgments: they say the move was good or bad for the measurement,
and which raw direction that means depends on the measurement. The classifier
translates every judgment into a raw direction through the polarity table in
query.polarity, on both the expected side and the reported side, and then
compares raw against raw (ADR 0007). A judgment on either side with no polarity
in the table gives INDIRECT.
"""

from datetime import UTC, datetime

from evidence_dossier.model import (
    ComparabilityLevel,
    EvidenceClaim,
    QueryProposition,
    ResultDirection,
    Stance,
    StanceAssessment,
)
from evidence_dossier.query.comparability import ComparabilityAssessment
from evidence_dossier.query.polarity import POLARITY_VERSION, Polarity, polarity_of

_NULL = frozenset({ResultDirection.UNCHANGED, ResultDirection.NOT_OBSERVED})
# Directions that judge the move instead of naming it. They need the polarity table.
_JUDGMENT = frozenset({ResultDirection.IMPROVED, ResultDirection.WORSENED})
_TOO_LOW = frozenset({ComparabilityLevel.LOW, ComparabilityLevel.INCOMPATIBLE})


class StanceClassifier:
    """Assigns a query relative stance from the result direction and the comparability."""

    def classify(
        self,
        proposition: QueryProposition,
        claim: EvidenceClaim,
        assessment: ComparabilityAssessment,
    ) -> StanceAssessment:
        stance, reason = _decide(proposition, claim, assessment)
        return StanceAssessment(
            query_id=proposition.id,
            claim_id=claim.id,
            stance=stance,
            comparability=assessment.level,
            reason=f"{reason} The stance rules use polarity table {POLARITY_VERSION}.",
            created_at=datetime.now(UTC),
        )


def _decide(
    proposition: QueryProposition, claim: EvidenceClaim, assessment: ComparabilityAssessment
) -> tuple[Stance, str]:
    if assessment.level in _TOO_LOW:
        failed = "subject" if not assessment.matched("subject") else "measurement"
        return Stance.INSUFFICIENTLY_COMPARABLE, (
            f"Comparability is {assessment.level} because the {failed} dimension does not match."
        )
    if not assessment.matched("evidence directness"):
        return Stance.INDIRECT, (
            "The subject and outcome match, but the evidence directness dimension fails:"
            " the claim does not measure the proposition measurement itself."
        )
    actual = claim.result.direction
    expected = proposition.expected_direction
    if expected is None:
        return Stance.INDIRECT, "The proposition states no expected direction to compare against."
    if actual is ResultDirection.MIXED:
        return Stance.MIXED, "The claim reports a mixed result across its conditions."
    if actual in _NULL:
        return Stance.NULL, (
            f"The claim reports {actual}, {_significance(claim)}, so the result is null"
            f" against the expected {expected}."
        )
    if actual in (ResultDirection.UNKNOWN, ResultDirection.OBSERVED):
        return Stance.INDIRECT, f"The claim reports {actual}, which gives no direction to compare."
    if expected in _JUDGMENT or actual in _JUDGMENT:
        return _through_polarity(proposition, claim, expected, actual)
    if expected is actual:
        return Stance.SUPPORTS, f"The claim direction {actual} matches the expected {expected}."
    return Stance.CONTRADICTS, (
        f"The claim direction {actual} is opposite to the expected {expected}."
    )


def _through_polarity(
    proposition: QueryProposition,
    claim: EvidenceClaim,
    expected: ResultDirection,
    actual: ResultDirection,
) -> tuple[Stance, str]:
    """Translate each judgment into a raw direction, then compare the two raw directions."""
    name = _measurement_name(proposition, claim)
    polarity = polarity_of(name)
    if polarity is None:
        return Stance.INDIRECT, (
            f"The expected {expected} or the reported {actual} judges the measurement"
            f" '{name}', and that measurement is not in table {POLARITY_VERSION},"
            " so the two directions cannot be compared."
        )
    expected_raw = _translate(expected, polarity)
    actual_raw = _translate(actual, polarity)
    if expected_raw is actual_raw:
        return Stance.SUPPORTS, (
            f"The claim direction {actual} matches the expected {expected}, both as"
            f" {actual_raw}, because the measurement '{name}' is {polarity}."
        )
    return Stance.CONTRADICTS, (
        f"The claim direction {actual} is opposite to the expected {expected}, as"
        f" {actual_raw} against {expected_raw}, because the measurement '{name}'"
        f" is {polarity}."
    )


def _translate(direction: ResultDirection, polarity: Polarity) -> ResultDirection:
    """Restate a judgment as the raw direction that the polarity gives it."""
    if direction not in _JUDGMENT:
        return direction
    lower_is_better = polarity is Polarity.LOWER_IS_BETTER
    if direction is ResultDirection.IMPROVED:
        return ResultDirection.DECREASED if lower_is_better else ResultDirection.INCREASED
    return ResultDirection.INCREASED if lower_is_better else ResultDirection.DECREASED


def _measurement_name(proposition: QueryProposition, claim: EvidenceClaim) -> str:
    """Name the measurement for the lookup: the claim name first, the proposition name after."""
    name = None if claim.measurement is None else claim.measurement.name
    if name is not None:
        return name.canonical or name.original
    return proposition.measurement or ""


def _significance(claim: EvidenceClaim) -> str:
    """State the significance flag in words, for the null reason sentence."""
    if claim.result.statistical_significance:
        return "reported as significant"
    return "no significance reported"
