"""Retrieval, stance and comparability scoring with hand computed expected values."""

import pytest

from evidence_dossier.evaluate import (
    Dataset,
    GoldRetrieval,
    run_retrieval_evaluation,
    run_stance_evaluation,
)
from evidence_dossier.model import ComparabilityLevel
from tests.evaluate_predictions import B1, B2, RANKINGS, STANCE_PREDICTIONS, fixture_dataset


def test_retrieval_per_query_and_means() -> None:
    result = run_retrieval_evaluation(fixture_dataset(), RANKINGS)
    q1, q2, q3 = result.per_query
    assert q1.recall_at_5 == pytest.approx(1 / 3)
    assert (q1.recall_at_10, q1.precision_at_10) == (1.0, 0.3)
    assert (q2.recall_at_5, q2.recall_at_10, q2.precision_at_10) == (1.0, 1.0, 0.1)
    assert (q3.returned, q3.recall_at_5, q3.precision_at_10) == (0, 0.0, 0.0)
    assert result.recall_at_5 == pytest.approx(4 / 9)
    assert result.recall_at_10 == pytest.approx(2 / 3)
    assert result.precision_at_10 == pytest.approx(0.4 / 3)


def test_retrieval_without_relevant_claims_is_not_assessable() -> None:
    dataset = Dataset(split="dev", retrievals=(GoldRetrieval(query_id="q", query_text="t"),))
    result = run_retrieval_evaluation(dataset, {"q": ["a", "a", "b"]})
    assert result.per_query[0].returned == 2
    assert result.recall_at_5 is None
    assert result.precision_at_10 == 0.0
    assert run_retrieval_evaluation(Dataset(split="dev"), {}).precision_at_10 is None


def test_stance_per_class_macro_and_confusion() -> None:
    result = run_stance_evaluation(fixture_dataset(), STANCE_PREDICTIONS)
    assert (result.labeled, result.missing, result.extra) == (9, 1, 1)
    per = result.per_class
    assert per["SUPPORTS"].precision == pytest.approx(2 / 3)
    assert per["SUPPORTS"].f1 == pytest.approx(0.8)
    assert per["NULL"].f1 == 1.0
    assert (per["CONTRADICTS"].precision, per["CONTRADICTS"].recall, per["CONTRADICTS"].f1) == (
        None,
        0.0,
        0.0,
    )
    assert per["MIXED"].f1 is None
    assert per["INDIRECT"].f1 == pytest.approx(2 / 3)
    assert per["INSUFFICIENTLY_COMPARABLE"].recall == 0.5
    assert result.macro_f1 == pytest.approx((0.8 + 1 + 0 + 2 / 3 + 2 / 3) / 5)
    assert result.confusion["CONTRADICTS"]["SUPPORTS"] == 1
    assert result.confusion["INSUFFICIENTLY_COMPARABLE"] == {
        "SUPPORTS": 0, "CONTRADICTS": 0, "NULL": 0, "MIXED": 0, "INDIRECT": 1, "INSUFFICIENTLY_COMPARABLE": 1,
    }  # fmt: skip
    assert sum(sum(row.values()) for row in result.confusion.values()) == 8


def test_comparability_accuracy_and_incompatible_misses() -> None:
    result = run_stance_evaluation(fixture_dataset(), STANCE_PREDICTIONS)
    assert result.comparability_accuracy == 0.625
    (miss,) = result.comparability_misses
    assert (miss.query_id, miss.claim_id, miss.predicted) == (
        "q1",
        f"{B2}:c1",
        ComparabilityLevel.LOW,
    )
    assert miss.reason.startswith("both works")
    assert B1 in RANKINGS["q1"][0]


def test_stance_without_predictions_is_not_assessable() -> None:
    result = run_stance_evaluation(fixture_dataset(), [])
    assert result.missing == 9
    assert result.macro_f1 is None
    assert result.comparability_accuracy is None
    assert all(p.f1 is None for p in result.per_class.values())
