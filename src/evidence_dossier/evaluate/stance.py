"""Stance and comparability scoring over labeled query and claim pairs (plan section 50).

A prediction joins a gold label on (query_id, claim_id). A gold pair without a
prediction counts as missing, and a prediction without a gold pair is ignored.
Both counts appear in the result.
"""

from collections.abc import Sequence

from evidence_dossier.evaluate.gold import Dataset
from evidence_dossier.evaluate.scores import PRF, Counts, ratio
from evidence_dossier.model import ComparabilityLevel, FrozenModel, Stance


class StancePrediction(FrozenModel):
    """One predicted stance record (plan section 39), with the reason the classifier gave."""

    query_id: str
    claim_id: str
    stance: Stance
    comparability: ComparabilityLevel
    reason: str = ""


class ComparabilityMiss(FrozenModel):
    """A pair the annotator marked INCOMPATIBLE that the prediction treated as comparable."""

    query_id: str
    claim_id: str
    predicted: ComparabilityLevel
    reason: str


class StanceEvaluation(FrozenModel):
    labeled: int
    missing: int
    extra: int
    per_class: dict[str, PRF]
    macro_f1: float | None
    # Gold stance to predicted stance to count, over the six Stance values.
    confusion: dict[str, dict[str, int]]
    comparability_accuracy: float | None
    comparability_misses: tuple[ComparabilityMiss, ...]


def run_stance_evaluation(
    gold: Dataset, predictions: Sequence[StancePrediction]
) -> StanceEvaluation:
    predicted = {(p.query_id, p.claim_id): p for p in predictions}
    labels = sorted(gold.stances, key=lambda s: (s.query_id, s.claim_id))
    confusion = {g: dict.fromkeys(Stance, 0) for g in Stance}
    counts = dict.fromkeys(Stance, Counts())
    misses: list[ComparabilityMiss] = []
    scored = comparable_correct = 0
    for label in labels:
        prediction = predicted.get((label.query_id, label.claim_id))
        if prediction is None:
            continue
        scored += 1
        confusion[label.stance][prediction.stance] += 1
        if prediction.stance == label.stance:
            counts[label.stance] += Counts(true_positives=1)
        else:
            counts[label.stance] += Counts(false_negatives=1)
            counts[prediction.stance] += Counts(false_positives=1)
        if prediction.comparability == label.comparability:
            comparable_correct += 1
        if (
            label.comparability is ComparabilityLevel.INCOMPATIBLE
            and prediction.comparability is not ComparabilityLevel.INCOMPATIBLE
        ):
            misses.append(
                ComparabilityMiss(
                    query_id=label.query_id,
                    claim_id=label.claim_id,
                    predicted=prediction.comparability,
                    reason=prediction.reason,
                )
            )
    per_class = {stance.value: PRF.from_counts(c) for stance, c in counts.items()}
    gold_pairs = {(s.query_id, s.claim_id) for s in labels}
    return StanceEvaluation(
        labeled=len(labels),
        missing=len(labels) - scored,
        extra=len(set(predicted) - gold_pairs),
        per_class=per_class,
        macro_f1=PRF.macro(per_class.values()).f1,
        confusion={g.value: {p.value: n for p, n in row.items()} for g, row in confusion.items()},
        comparability_accuracy=ratio(comparable_correct, scored),
        comparability_misses=tuple(misses),
    )
