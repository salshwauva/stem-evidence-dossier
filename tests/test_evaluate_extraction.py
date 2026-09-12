"""Extraction, relationship and span scoring with hand computed expected values.

The predictions in tests/evaluate_predictions.py give these counts over the
eight scored fields: 37 true positives, 11 false positives, 18 false negatives.
"""

import pytest

from evidence_dossier.evaluate import (
    Dataset,
    match_claims,
    run_extraction_evaluation,
    span_jaccard,
    spans_overlap,
)
from evidence_dossier.evaluate.extraction import ExtractionEvaluation
from evidence_dossier.model import EvidenceSpan
from tests.evaluate_predictions import (
    B1,
    B2,
    C1,
    C2,
    STUDY_MAP,
    fixture_dataset,
    fixture_predictions,
)


def _span(section: str, start: int, end: int) -> EvidenceSpan:
    return EvidenceSpan(
        research_work_id="w",
        section_id=section,
        start_offset=start,
        end_offset=end,
        source_text="x",
    )


@pytest.fixture(scope="module")
def evaluation() -> ExtractionEvaluation:
    dataset = fixture_dataset()
    return run_extraction_evaluation(dataset, fixture_predictions(dataset), study_map=STUDY_MAP)


def test_jaccard_overlap_rule() -> None:
    assert span_jaccard(_span("s", 0, 10), _span("s", 5, 15)) == pytest.approx(5 / 15)
    assert span_jaccard(_span("s", 0, 10), _span("t", 0, 10)) == 0.0
    assert span_jaccard(_span("s", 0, 10), _span("s", 10, 20)) == 0.0
    assert spans_overlap(_span("s", 0, 10), _span("s", 5, 10))
    assert not spans_overlap(_span("s", 0, 10), _span("s", 6, 12))


def test_matching_is_one_to_one_and_greedy_on_the_best_overlap() -> None:
    dataset = fixture_dataset()
    matching = match_claims(dataset.claims, tuple(fixture_predictions(dataset)))
    assert [(g.claim_key, p.id) for g, p in matching.pairs] == [
        (f"{B1}:c1", "p1"),
        (f"{B2}:c1", "p4"),
        (f"{C1}:c1", "p5"),
        (f"{C1}:c2", "p6"),
        (f"{B1}:c2", "p2"),
    ]
    assert [g.claim_key for g in matching.unmatched_gold] == [f"{B1}:c3", f"{C2}:c1"]
    assert [p.id for p in matching.unmatched_predicted] == ["p7"]


def test_micro_and_macro_field_scores(evaluation: ExtractionEvaluation) -> None:
    micro = evaluation.fields.micro
    assert micro.precision == pytest.approx(37 / 48)
    assert micro.recall == pytest.approx(37 / 55)
    assert micro.f1 == pytest.approx(74 / 103)
    assert micro.support == 55
    # The unweighted mean of eight F1 values: seven of them over 13 and one of 5/6.
    assert evaluation.fields.macro.f1 == pytest.approx((64 / 13 + 5 / 6) / 8)


def test_per_field_scores(evaluation: ExtractionEvaluation) -> None:
    fields = evaluation.fields.per_field
    assert list(fields) == [
        "claim_type", "subject", "predicate", "outcome",
        "method", "comparator", "measurement", "result_direction",
    ]  # fmt: skip
    assert fields["claim_type"].f1 == pytest.approx(10 / 13)
    assert fields["subject"].precision == pytest.approx(4 / 6)
    assert fields["subject"].recall == pytest.approx(4 / 7)
    assert fields["comparator"].f1 == pytest.approx(5 / 6)
    assert fields["measurement"].f1 == pytest.approx(8 / 13)
    assert fields["result_direction"].recall == pytest.approx(4 / 7)


def test_field_errors_name_the_pair_and_both_values(evaluation: ExtractionEvaluation) -> None:
    errors = {
        (e.gold_key, e.field): (e.gold_value, e.predicted_value) for e in evaluation.field_errors
    }
    assert errors == {
        (f"{B2}:c1", "subject"): ("trl9 knockout", "knockout of the gene trl9"),
        (f"{C1}:c2", "measurement"): ("latency", "latency per query"),
        (f"{B1}:c2", "result_direction"): ("UNCHANGED", "DECREASED"),
    }
    assert evaluation.unmatched_gold == (f"{B1}:c3", f"{C2}:c1")
    assert evaluation.unmatched_predicted == ("p7",)


def test_scores_by_domain_and_source_level(evaluation: ExtractionEvaluation) -> None:
    assert list(evaluation.by_domain) == ["BIOLOGY", "COMPUTER_SCIENCE"]
    assert evaluation.by_domain["BIOLOGY"].micro.precision == pytest.approx(22 / 24)
    assert evaluation.by_domain["BIOLOGY"].micro.recall == pytest.approx(22 / 31)
    assert evaluation.by_domain["COMPUTER_SCIENCE"].micro.precision == 0.625
    assert list(evaluation.by_source_level) == ["ABSTRACT_ONLY", "FULL_TEXT"]
    assert evaluation.by_source_level["ABSTRACT_ONLY"].micro.recall == pytest.approx(7 / 16)
    assert evaluation.by_source_level["FULL_TEXT"].micro.recall == pytest.approx(30 / 39)


def test_relationship_credit_needs_the_study_and_the_three_entities(
    evaluation: ExtractionEvaluation,
) -> None:
    r = evaluation.relationships
    assert (r.matched, r.correct, r.rate) == (5, 3, 0.6)
    assert [(e.predicted_id, e.reason) for e in r.errors] == [
        ("p6", "measurement differs"),
        ("p2", "study s-bio1-cells is not the study of bio1-larvae"),
    ]


def test_span_rates_and_mismatches(evaluation: ExtractionEvaluation) -> None:
    s = evaluation.spans
    assert (s.gold_claims, s.exact_matches, s.overlap_matches) == (7, 4, 5)
    assert s.exact_rate == pytest.approx(4 / 7)
    assert s.overlap_rate == pytest.approx(5 / 7)
    (mismatch,) = s.mismatches
    assert mismatch.predicted_id == "p2"
    assert mismatch.predicted_offsets[0] == mismatch.gold_offsets[0] + 5


def test_empty_denominators_give_none() -> None:
    evaluation = run_extraction_evaluation(Dataset(split="dev"), [], study_map={})
    assert evaluation.fields.micro.precision is None
    assert evaluation.fields.micro.f1 is None
    assert evaluation.fields.macro.f1 is None
    assert evaluation.relationships.rate is None
    assert evaluation.spans.exact_rate is None
    assert evaluation.by_domain == {}
