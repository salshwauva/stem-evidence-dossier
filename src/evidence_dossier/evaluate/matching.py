"""Claim matching on evidence spans, with the overlap rule from the annotation guidelines.

Two spans overlap when they name the same section and the Jaccard index of
their character ranges is at least 0.5. Matching is greedy on the highest
Jaccard value, then on the gold key and the predicted ID, so it is one to one
and the same on every run.
"""

from evidence_dossier.evaluate.gold import GoldClaim
from evidence_dossier.model import EvidenceClaim, EvidenceSpan, FrozenModel

OVERLAP_THRESHOLD = 0.5


def span_jaccard(gold: EvidenceSpan, predicted: EvidenceSpan) -> float:
    """Return the Jaccard index of the two character ranges, or 0.0 across sections."""
    if gold.section_id != predicted.section_id:
        return 0.0
    intersection = min(gold.end_offset, predicted.end_offset) - max(
        gold.start_offset, predicted.start_offset
    )
    if intersection <= 0:
        return 0.0
    union = max(gold.end_offset, predicted.end_offset) - min(
        gold.start_offset, predicted.start_offset
    )
    return intersection / union


def spans_overlap(gold: EvidenceSpan, predicted: EvidenceSpan) -> bool:
    return span_jaccard(gold, predicted) >= OVERLAP_THRESHOLD


class Matching(FrozenModel):
    """The one to one pairs between gold and predicted claims, and the claims left over."""

    pairs: tuple[tuple[GoldClaim, EvidenceClaim], ...]
    unmatched_gold: tuple[GoldClaim, ...]
    unmatched_predicted: tuple[EvidenceClaim, ...]


def match_claims(gold: tuple[GoldClaim, ...], predicted: tuple[EvidenceClaim, ...]) -> Matching:
    candidates = sorted(
        (
            (-span_jaccard(g.evidence_span, p.evidence_span), g.claim_key, p.id, gi, pi)
            for gi, g in enumerate(gold)
            for pi, p in enumerate(predicted)
            if g.research_work_id == p.research_work_id
            and spans_overlap(g.evidence_span, p.evidence_span)
        ),
    )
    taken_gold: set[int] = set()
    taken_predicted: set[int] = set()
    pairs: list[tuple[GoldClaim, EvidenceClaim]] = []
    for _, _, _, gi, pi in candidates:
        if gi in taken_gold or pi in taken_predicted:
            continue
        taken_gold.add(gi)
        taken_predicted.add(pi)
        pairs.append((gold[gi], predicted[pi]))
    return Matching(
        pairs=tuple(pairs),
        unmatched_gold=tuple(g for i, g in enumerate(gold) if i not in taken_gold),
        unmatched_predicted=tuple(p for i, p in enumerate(predicted) if i not in taken_predicted),
    )
