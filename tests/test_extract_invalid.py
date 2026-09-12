"""Invalid replies are stored as INVALID runs with their errors, and no claim is stored."""

import json
from collections.abc import Iterator
from typing import Any

import pytest

from evidence_dossier.extract import extract_document
from evidence_dossier.model import ValidationStatus
from evidence_dossier.normalize import normalize_claim
from evidence_dossier.store import Store
from tests.extract_support import NOW, Corpus, add_paper, paper_corpus, valid_response

OTHER_TEXT = "The other paper reached 80.0 percent top-1 accuracy on Benchmark Y."


@pytest.fixture
def corpus() -> Iterator[Corpus]:
    with Store(":memory:") as store:
        yield paper_corpus(store)


def _edited(claim_index: int, **fields: Any) -> str:
    """Return the valid reply with the given fields set on one claim."""
    data = json.loads(valid_response())
    claim = data["claims"][claim_index]
    for name, value in fields.items():
        if isinstance(value, dict):
            claim[name] = {**claim[name], **value}
        else:
            claim[name] = value
    return json.dumps(data)


CASES = {
    "malformed_json": ('{"studies": [', "response is not JSON"),
    "unknown_claim_type": (
        _edited(0, claim_type="PERFORMANCE_GAIN"),
        "claims.0.claim_type: Input should be",
    ),
    "unknown_study_key": (
        _edited(1, study_key="latency"),
        "claims.1.study_key: latency is not a study of this output",
    ),
    "unknown_field": (
        _edited(2, offsets=[3, 9]),
        "claims.2.offsets: Extra inputs are not permitted",
    ),
    "source_text_not_found": (
        _edited(0, evidence={"source_text": "ResNet50 reached 79.1 percent"}),
        "claims.0.evidence.source_text: does not occur in section",
    ),
    "source_text_found_twice": (
        _edited(1, evidence={"source_text": "images per second"}),
        "claims.1.evidence.source_text: occurs 2 times in section",
    ),
    "span_in_another_document": (
        _edited(2, evidence={"section_id": "{other}", "source_text": "reached 80.0 percent"}),
        "claims.2.evidence.section_id: {other} is not a section of document",
    ),
}


@pytest.mark.parametrize("case", CASES, ids=CASES)
def test_invalid_reply_stores_an_invalid_run_and_no_claim(corpus: Corpus, case: str) -> None:
    other = add_paper(corpus.store, "2409.00002", (OTHER_TEXT,))
    text, expected = (value.replace("{other}", other.sections[0].id) for value in CASES[case])

    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(text),
        normalizer=normalize_claim,
        now=NOW,
    )

    assert run.validation_status is ValidationStatus.INVALID
    assert run.raw_response == text
    assert any(expected in error for error in run.errors), run.errors
    stored = corpus.store.get_extraction_run(run.id)
    assert stored is not None and stored.errors == run.errors
    assert corpus.store.list_claims() == []
    assert corpus.store.get_study(f"{corpus.document.id}_accuracy") is None
