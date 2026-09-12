"""The report on the dev fixture equals the checked-in expected markdown.

To regenerate after a deliberate change, run the test with
EVALUATE_REPORT_WRITE=1 and read the diff before the commit.
"""

import os
from datetime import UTC, datetime

import pytest

from evidence_dossier.evaluate import (
    NOT_ASSESSABLE,
    Dataset,
    EvaluationReport,
    run_extraction_evaluation,
    run_retrieval_evaluation,
    run_stance_evaluation,
)
from tests.evaluate_predictions import (
    FIXTURE_DIR,
    RANKINGS,
    STANCE_PREDICTIONS,
    STUDY_MAP,
    fixture_dataset,
    fixture_predictions,
)

CREATED_AT = datetime(2026, 9, 12, 6, 0, tzinfo=UTC)


def _report(dataset: Dataset, predict: bool = True) -> EvaluationReport:
    predicted = fixture_predictions(dataset) if predict else []
    return EvaluationReport(
        model_identifier="extractor-model-a",
        prompt_version="claims-v1",
        schema_version="core-1",
        split=dataset.split,
        created_at=CREATED_AT,
        extraction=run_extraction_evaluation(dataset, predicted, study_map=STUDY_MAP),
        retrieval=run_retrieval_evaluation(dataset, RANKINGS),
        stance=run_stance_evaluation(dataset, STANCE_PREDICTIONS),
        notes=(
            "The papers, the gold labels and the predictions are invented test fixtures.",
            "The predictions were written by hand from the gold labels with deliberate errors.",
        ),
    )


@pytest.mark.skipif(
    os.environ.get("EVALUATE_REPORT_WRITE") != "1",
    reason="set EVALUATE_REPORT_WRITE=1 to regenerate",
)
def test_regenerate_the_expected_file() -> None:
    """Rewrites the snapshot. It never asserts, so the comparison test below stays honest."""
    (FIXTURE_DIR / "expected_report.md").write_text(_report(fixture_dataset()).to_markdown())


def test_markdown_matches_the_expected_file() -> None:
    expected_path = FIXTURE_DIR / "expected_report.md"
    markdown = _report(fixture_dataset()).to_markdown()
    assert markdown == expected_path.read_text()


def test_markdown_is_deterministic_and_names_the_errors() -> None:
    dataset = fixture_dataset()
    first, second = _report(dataset).to_markdown(), _report(dataset).to_markdown()
    assert first == second
    assert "| work_bio_0002:c1 | p4 | subject |" in first
    assert "study s-bio1-cells is not the study of bio1-larvae" in first
    assert "| work_bio_0001:c2 | p2 | " in first
    assert "—" not in first and "–" not in first


def test_empty_report_says_not_assessable() -> None:
    markdown = _report(Dataset(split="test"), predict=False).to_markdown()
    assert f"| micro | {NOT_ASSESSABLE} | {NOT_ASSESSABLE} | {NOT_ASSESSABLE} | 0 |" in markdown
    assert f"- Recall@5: {NOT_ASSESSABLE}" in markdown
    assert f"- Macro F1: {NOT_ASSESSABLE}" in markdown
    assert " 0.000 " not in markdown.split("## Retrieval")[0]


def test_sections_that_did_not_run_say_so() -> None:
    report = EvaluationReport(
        model_identifier="m",
        prompt_version="p",
        schema_version="s",
        split="dev",
        created_at=CREATED_AT,
    )
    assert report.to_markdown().count("Not run.") == 3
