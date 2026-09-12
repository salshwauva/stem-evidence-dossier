"""Extraction, relationship and evidence span scoring (plan section 50).

Field values compare after normalization equivalence from the annotation
guidelines: the canonical form when one is set, else the original text, with
case folded and surrounding whitespace removed. A matched pair with different
values counts one false positive and one false negative. An unmatched
predicted claim counts a false positive for every value it carries, and an
unmatched gold claim a false negative for every value it carries.
"""

from collections.abc import Callable, Mapping, Sequence

from evidence_dossier.evaluate.gold import Dataset, GoldClaim
from evidence_dossier.evaluate.matching import Matching, match_claims
from evidence_dossier.evaluate.scores import PRF, Counts, ratio
from evidence_dossier.model import EvidenceClaim, FrozenModel, Term

type Claim = GoldClaim | EvidenceClaim
type FieldGetter = Callable[[Claim], str | None]


def term_value(term: Term | None) -> str | None:
    """The value that scoring compares: the canonical form, else the original text."""
    if term is None:
        return None
    return (term.canonical or term.original).casefold().strip()


def _plain(value: str | None) -> str | None:
    return None if value is None else value.casefold().strip()


FIELDS: dict[str, FieldGetter] = {
    "claim_type": lambda c: c.claim_type.value,
    "subject": lambda c: term_value(c.subject),
    "predicate": lambda c: _plain(c.predicate),
    "outcome": lambda c: _plain(c.outcome),
    "method": lambda c: None if c.method is None else term_value(c.method.name),
    "comparator": lambda c: None if c.comparator is None else term_value(c.comparator.name),
    "measurement": lambda c: None if c.measurement is None else term_value(c.measurement.name),
    "result_direction": lambda c: c.result.direction.value,
}


class FieldError(FrozenModel):
    """One field of one matched pair where the values differ."""

    gold_key: str
    predicted_id: str
    field: str
    gold_value: str | None
    predicted_value: str | None


class FieldScores(FrozenModel):
    """Per field precision, recall and F1 with the micro and macro aggregates."""

    per_field: dict[str, PRF]
    micro: PRF
    macro: PRF


class RelationshipError(FrozenModel):
    gold_key: str
    predicted_id: str
    reason: str


class RelationshipScore(FrozenModel):
    """Credit for matched claims whose study and whose method, comparator and measurement agree."""

    matched: int
    correct: int
    rate: float | None
    errors: tuple[RelationshipError, ...]


class SpanMismatch(FrozenModel):
    gold_key: str
    predicted_id: str
    gold_offsets: tuple[int, int]
    predicted_offsets: tuple[int, int]


class SpanScore(FrozenModel):
    """Exact and overlap match rates over the gold claims."""

    gold_claims: int
    exact_matches: int
    overlap_matches: int
    exact_rate: float | None
    overlap_rate: float | None
    mismatches: tuple[SpanMismatch, ...]


class ExtractionEvaluation(FrozenModel):
    fields: FieldScores
    by_domain: dict[str, FieldScores]
    by_source_level: dict[str, FieldScores]
    field_errors: tuple[FieldError, ...]
    unmatched_gold: tuple[str, ...]
    unmatched_predicted: tuple[str, ...]
    relationships: RelationshipScore
    spans: SpanScore


def _field_counts(matching: Matching) -> tuple[dict[str, Counts], list[FieldError]]:
    counts = dict.fromkeys(FIELDS, Counts())
    errors: list[FieldError] = []
    for name, get in FIELDS.items():
        for gold, predicted in matching.pairs:
            g, p = get(gold), get(predicted)
            if g == p:
                if g is not None:
                    counts[name] += Counts(true_positives=1)
                continue
            counts[name] += Counts(
                false_positives=int(p is not None), false_negatives=int(g is not None)
            )
            errors.append(
                FieldError(
                    gold_key=gold.claim_key,
                    predicted_id=predicted.id,
                    field=name,
                    gold_value=g,
                    predicted_value=p,
                )
            )
        for gold in matching.unmatched_gold:
            counts[name] += Counts(false_negatives=int(get(gold) is not None))
        for predicted in matching.unmatched_predicted:
            counts[name] += Counts(false_positives=int(get(predicted) is not None))
    return counts, errors


def score_fields(matching: Matching) -> tuple[FieldScores, tuple[FieldError, ...]]:
    counts, errors = _field_counts(matching)
    per_field = {name: PRF.from_counts(c) for name, c in counts.items()}
    total = Counts()
    for c in counts.values():
        total += c
    scores = FieldScores(
        per_field=per_field, micro=PRF.from_counts(total), macro=PRF.macro(per_field.values())
    )
    return scores, tuple(errors)


def _grouped(matching: Matching, key: Callable[[Claim], str]) -> dict[str, FieldScores]:
    groups = sorted(
        {key(c) for c in matching.unmatched_gold}
        | {key(c) for c in matching.unmatched_predicted}
        | {key(g) for g, _ in matching.pairs}
    )
    result: dict[str, FieldScores] = {}
    for group in groups:
        part = Matching(
            pairs=tuple(pair for pair in matching.pairs if key(pair[0]) == group),
            unmatched_gold=tuple(c for c in matching.unmatched_gold if key(c) == group),
            unmatched_predicted=tuple(c for c in matching.unmatched_predicted if key(c) == group),
        )
        result[group] = score_fields(part)[0]
    return result


def score_relationships(matching: Matching, study_map: Mapping[str, str]) -> RelationshipScore:
    """Credit a matched pair only when the study agrees and the three entities agree.

    study_map maps a gold study key to the predicted study ID. A correct entity
    on the wrong study earns nothing (plan section 50).
    """
    errors: list[RelationshipError] = []
    for gold, predicted in matching.pairs:
        reasons: list[str] = []
        expected = study_map.get(gold.study_key)
        if expected != predicted.study_id:
            reasons.append(f"study {predicted.study_id} is not the study of {gold.study_key}")
        for name in ("method", "comparator", "measurement"):
            if FIELDS[name](gold) != FIELDS[name](predicted):
                reasons.append(f"{name} differs")
        if reasons:
            errors.append(
                RelationshipError(
                    gold_key=gold.claim_key, predicted_id=predicted.id, reason="; ".join(reasons)
                )
            )
    matched = len(matching.pairs)
    correct = matched - len(errors)
    return RelationshipScore(
        matched=matched, correct=correct, rate=ratio(correct, matched), errors=tuple(errors)
    )


def score_spans(matching: Matching) -> SpanScore:
    mismatches: list[SpanMismatch] = []
    for gold, predicted in matching.pairs:
        g, p = gold.evidence_span, predicted.evidence_span
        if (g.start_offset, g.end_offset) != (p.start_offset, p.end_offset):
            mismatches.append(
                SpanMismatch(
                    gold_key=gold.claim_key,
                    predicted_id=predicted.id,
                    gold_offsets=(g.start_offset, g.end_offset),
                    predicted_offsets=(p.start_offset, p.end_offset),
                )
            )
    total = len(matching.pairs) + len(matching.unmatched_gold)
    overlap = len(matching.pairs)
    exact = overlap - len(mismatches)
    return SpanScore(
        gold_claims=total,
        exact_matches=exact,
        overlap_matches=overlap,
        exact_rate=ratio(exact, total),
        overlap_rate=ratio(overlap, total),
        mismatches=tuple(mismatches),
    )


def run_extraction_evaluation(
    gold: Dataset, predicted: Sequence[EvidenceClaim], *, study_map: Mapping[str, str]
) -> ExtractionEvaluation:
    """Score predicted claims against the gold claims of the dataset.

    A predicted claim for a work outside the dataset has no gold claim to match
    and counts as false positives. Source level comes from the gold document of
    the work; a claim for an unknown work reports the level "UNKNOWN".
    """
    matching = match_claims(gold.claims, tuple(predicted))
    levels = {d.research_work_id: d.source_level.value for d in gold.documents}

    def source_level(claim: Claim) -> str:
        return levels.get(claim.research_work_id, "UNKNOWN")

    fields, errors = score_fields(matching)
    return ExtractionEvaluation(
        fields=fields,
        by_domain=_grouped(matching, lambda c: c.research_context.domain.value),
        by_source_level=_grouped(matching, source_level),
        field_errors=errors,
        unmatched_gold=tuple(c.claim_key for c in matching.unmatched_gold),
        unmatched_predicted=tuple(c.id for c in matching.unmatched_predicted),
        relationships=score_relationships(matching, study_map),
        spans=score_spans(matching),
    )
