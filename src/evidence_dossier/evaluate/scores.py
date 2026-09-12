"""Score records and the arithmetic they share.

Every score is a float in [0, 1]. An empty denominator gives None, never a
placeholder 0 or 1, so a report cannot claim a result it did not measure.
"""

from collections.abc import Iterable

from evidence_dossier.model import FrozenModel


def ratio(numerator: int, denominator: int) -> float | None:
    """Return numerator / denominator, or None when the denominator is zero."""
    return None if denominator == 0 else numerator / denominator


def mean(values: Iterable[float | None]) -> float | None:
    """Return the mean of the values that are not None, or None when there is none."""
    present = [v for v in values if v is not None]
    return None if not present else sum(present) / len(present)


class Counts(FrozenModel):
    """True positives, false positives and false negatives for one field or one class."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
        )

    @property
    def precision(self) -> float | None:
        return ratio(self.true_positives, self.true_positives + self.false_positives)

    @property
    def recall(self) -> float | None:
        return ratio(self.true_positives, self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float | None:
        """The harmonic mean of precision and recall. None when both are None."""
        if self.precision is None and self.recall is None:
            return None
        p, r = self.precision or 0.0, self.recall or 0.0
        return 0.0 if p + r == 0 else 2 * p * r / (p + r)


class PRF(FrozenModel):
    """Precision, recall and F1 as stored values, so a report is plain data."""

    precision: float | None
    recall: float | None
    f1: float | None
    support: int

    @classmethod
    def from_counts(cls, counts: Counts) -> "PRF":
        return cls(
            precision=counts.precision,
            recall=counts.recall,
            f1=counts.f1,
            support=counts.true_positives + counts.false_negatives,
        )

    @classmethod
    def macro(cls, parts: Iterable["PRF"]) -> "PRF":
        """The unweighted mean over the parts. A part with no gold and no predictions drops out."""
        listed = list(parts)
        return cls(
            precision=mean(p.precision for p in listed),
            recall=mean(p.recall for p in listed),
            f1=mean(p.f1 for p in listed),
            support=sum(p.support for p in listed),
        )
