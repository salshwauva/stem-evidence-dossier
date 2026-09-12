"""Stance classifier: how a comparable claim relates to the proposition (plan section 39).

The classifier runs after the comparability engine and never changes the
candidate list. Every assessment carries a reason sentence and no probability.

Two rules follow the plan lists rather than the worked example in plan section 7.
A null family direction is NULL, because plan section 39 lists NULL next to
CONTRADICTS and plan section 21 keeps UNCHANGED and NOT_OBSERVED apart from the
opposite directions. A quality direction from plan section 21 (IMPROVED or
WORSENED) lines up with a magnitude direction (INCREASED or DECREASED) only
through the measurement polarity table in query.polarity (ADR 0007).
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

_DOWN = frozenset({ResultDirection.DECREASED, ResultDirection.WORSENED})
_UP = frozenset({ResultDirection.INCREASED, ResultDirection.IMPROVED})
_NULL = frozenset({ResultDirection.UNCHANGED, ResultDirection.NOT_OBSERVED})
_QUALITY = frozenset({ResultDirection.IMPROVED, ResultDirection.WORSENED})
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
    if (expected in _QUALITY) != (actual in _QUALITY):
        return _across_families(proposition, claim, expected, actual)
    if _family(actual) is _family(expected):
        return Stance.SUPPORTS, (
            f"The claim direction {actual} is in the same direction family as the expected {expected}."
        )
    return Stance.CONTRADICTS, (
        f"The claim direction {actual} is opposite to the expected {expected}."
    )


def _across_families(
    proposition: QueryProposition,
    claim: EvidenceClaim,
    expected: ResultDirection,
    actual: ResultDirection,
) -> tuple[Stance, str]:
    """Compare a quality direction with a magnitude direction through the polarity table."""
    name = _measurement_name(proposition, claim)
    polarity = polarity_of(name)
    if polarity is None:
        return Stance.INDIRECT, (
            f"The expected {expected} and the reported {actual} need the polarity of the"
            f" measurement '{name}', and that measurement is not in table {POLARITY_VERSION}."
        )
    if _translate(expected, polarity) is _translate(actual, polarity):
        return Stance.SUPPORTS, (
            f"The claim direction {actual} agrees with the expected {expected} because the"
            f" measurement '{name}' is {polarity}."
        )
    return Stance.CONTRADICTS, (
        f"The claim direction {actual} opposes the expected {expected} because the"
        f" measurement '{name}' is {polarity}."
    )


def _translate(direction: ResultDirection, polarity: Polarity) -> ResultDirection:
    """Restate a quality direction as the magnitude direction that the polarity gives it."""
    if direction not in _QUALITY:
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


def _family(direction: ResultDirection) -> frozenset[ResultDirection] | None:
    if direction in _DOWN:
        return _DOWN
    if direction in _UP:
        return _UP
    return None
