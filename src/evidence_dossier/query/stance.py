"""Stance classifier: how a comparable claim relates to the proposition (plan section 39).

The classifier runs after the comparability engine and never changes the
candidate list. Every assessment carries a reason sentence and no probability.
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

_DOWN = frozenset({ResultDirection.DECREASED, ResultDirection.WORSENED})
_UP = frozenset({ResultDirection.INCREASED, ResultDirection.IMPROVED})
_NULL = frozenset({ResultDirection.UNCHANGED, ResultDirection.NOT_OBSERVED})
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
            reason=reason,
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
        if claim.result.statistical_significance:
            return Stance.CONTRADICTS, (
                f"The claim reports {actual} with statistical significance,"
                f" against the expected {expected}."
            )
        return Stance.NULL, (
            f"The claim reports {actual} with statistical significance"
            f" {claim.result.statistical_significance}, so the result is null."
        )
    if actual in (ResultDirection.UNKNOWN, ResultDirection.OBSERVED):
        return Stance.INDIRECT, f"The claim reports {actual}, which gives no direction to compare."
    if expected is ResultDirection.DECREASED and actual is ResultDirection.IMPROVED:
        return Stance.SUPPORTS, (
            "The claim reports IMPROVED against an expected DECREASED; the rule treats"
            " an improvement as agreement when the proposition reduces an unwanted outcome."
        )
    if _family(actual) is _family(expected):
        return Stance.SUPPORTS, (
            f"The claim direction {actual} is in the same direction family as the expected {expected}."
        )
    return Stance.CONTRADICTS, (
        f"The claim direction {actual} is opposite to the expected {expected}."
    )


def _family(direction: ResultDirection) -> frozenset[ResultDirection] | None:
    if direction in _DOWN:
        return _DOWN
    if direction in _UP:
        return _UP
    return None
