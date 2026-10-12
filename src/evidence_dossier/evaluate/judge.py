"""Scores for the comparability judge against human labels (docs/judge-labeling-guidelines.md).

An arm is any source of verdicts for the same pairs: a model, the word rules, or a
judge that always answers unknown. The scorer takes verdicts as plain strings, so
this package never imports the query package (ADR 0008).

Only "match" counts as matched. A false match is a match verdict where the label is
anything else, and it is the costly error: it is the way a wrong claim reaches a
firm stance. A missed match is the reverse. An arm that answers unknown everywhere
has no false matches, so the gate also holds a floor on the matches it finds.
"""

from collections.abc import Mapping, Sequence
from typing import Literal

from evidence_dossier.evaluate.scores import ratio, wilson_interval
from evidence_dossier.model import FrozenModel

DIMENSIONS = ("subject", "comparator", "measurement")
MATCH = "match"
UNKNOWN = "unknown"
VERDICTS = frozenset({"match", "mismatch", "unknown", "inverse", "broader", "narrower"})

type Origin = Literal["retrieved", "reverse"]
type Verdicts = Mapping[str, Mapping[str, str]]
"""Pair ID to dimension to verdict. A dimension that was not asked is absent."""


class JudgePair(FrozenModel):
    """One query and claim pair of the benchmark."""

    pair_id: str
    query: str
    claim_id: str
    origin: Origin


class DimensionScore(FrozenModel):
    """The counts for one dimension, over the pairs that carry a label for it."""

    dimension: str
    pairs: int
    positives: int
    exact_agreements: int
    matched_agreements: int
    false_matches: int
    missed_matches: int
    unknowns: int
    unanswered: int

    @property
    def negatives(self) -> int:
        return self.pairs - self.positives

    @property
    def false_match_rate(self) -> float | None:
        return ratio(self.false_matches, self.negatives)

    @property
    def recall(self) -> float | None:
        return ratio(self.positives - self.missed_matches, self.positives)

    @property
    def false_match_interval(self) -> tuple[float, float] | None:
        return wilson_interval(self.false_matches, self.negatives)

    @property
    def agreement_interval(self) -> tuple[float, float] | None:
        return wilson_interval(self.matched_agreements, self.pairs)


class ArmScore(FrozenModel):
    """The scores of one arm, per dimension and summed."""

    arm: str
    dimensions: tuple[DimensionScore, ...]

    @property
    def total(self) -> DimensionScore:
        return DimensionScore(
            dimension="all",
            pairs=sum(d.pairs for d in self.dimensions),
            positives=sum(d.positives for d in self.dimensions),
            exact_agreements=sum(d.exact_agreements for d in self.dimensions),
            matched_agreements=sum(d.matched_agreements for d in self.dimensions),
            false_matches=sum(d.false_matches for d in self.dimensions),
            missed_matches=sum(d.missed_matches for d in self.dimensions),
            unknowns=sum(d.unknowns for d in self.dimensions),
            unanswered=sum(d.unanswered for d in self.dimensions),
        )


def score_arm(
    arm: str,
    labels: Verdicts,
    verdicts: Verdicts,
    pair_ids: Sequence[str] | None = None,
) -> ArmScore:
    """Score one arm's verdicts against the labels on the chosen pairs (all labeled pairs by default).

    A labeled dimension with no verdict is unanswered. It counts as a miss when the label
    is a match, and it counts for nothing else, so an arm cannot gain by staying silent.
    """
    chosen = list(labels) if pair_ids is None else list(pair_ids)
    for pair_id in chosen:
        for dimension, written in labels.get(pair_id, {}).items():
            if written not in VERDICTS:
                raise ValueError(f"pair {pair_id}: {dimension} label {written!r} is not a verdict")
    scores: list[DimensionScore] = []
    for dimension in DIMENSIONS:
        pairs = positives = exact = matched = false_matches = missed = unknowns = unanswered = 0
        for pair_id in chosen:
            label = labels.get(pair_id, {}).get(dimension)
            if label is None:
                continue
            pairs += 1
            positives += label == MATCH
            verdict = verdicts.get(pair_id, {}).get(dimension)
            if verdict is None:
                unanswered += 1
                missed += label == MATCH
                continue
            exact += verdict == label
            matched += (verdict == MATCH) == (label == MATCH)
            false_matches += verdict == MATCH and label != MATCH
            missed += verdict != MATCH and label == MATCH
            unknowns += verdict == UNKNOWN
        scores.append(
            DimensionScore(
                dimension=dimension,
                pairs=pairs,
                positives=positives,
                exact_agreements=exact,
                matched_agreements=matched,
                false_matches=false_matches,
                missed_matches=missed,
                unknowns=unknowns,
                unanswered=unanswered,
            )
        )
    return ArmScore(arm=arm, dimensions=tuple(scores))


class Gate(FrozenModel):
    """The pass rule for a judge arm, written before the test labels are opened."""

    # False matches may exceed the rules arm by at most this many.
    max_false_matches_over_rules: int = 0
    # Share of the labeled matches the arm must find. Blocks the arm that always says unknown.
    min_recall: float = 0.5
    # The arm's matched agreement may fall short of the rules arm by at most this much.
    max_agreement_drop_vs_rules: float = 0.0


class GateResult(FrozenModel):
    passed: bool
    reasons: tuple[str, ...]


def apply_gate(candidate: ArmScore, rules: ArmScore, gate: Gate) -> GateResult:
    """Decide whether an arm passes. Every failed condition gets a reason."""
    reasons: list[str] = []
    c, r = candidate.total, rules.total
    if c.false_matches > r.false_matches + gate.max_false_matches_over_rules:
        reasons.append(f"false matches {c.false_matches} exceed the rules arm's {r.false_matches}")
    recall = c.recall
    if recall is None or recall < gate.min_recall:
        shown = "none" if recall is None else f"{recall:.2f}"
        reasons.append(f"recall {shown} is under the floor {gate.min_recall:.2f}")
    c_agree, r_agree = ratio(c.matched_agreements, c.pairs), ratio(r.matched_agreements, r.pairs)
    if c_agree is None or r_agree is None or c_agree < r_agree - gate.max_agreement_drop_vs_rules:
        reasons.append("matched agreement is under the rules arm's")
    return GateResult(passed=not reasons, reasons=tuple(reasons))
