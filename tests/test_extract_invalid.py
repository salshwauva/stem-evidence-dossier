"""A reply that fails as a whole is an INVALID run with its errors, and no claim is stored.

A claim that fails a relationship check is rejected alone: the run is PARTIAL, and
the claims that passed are stored. A reply whose every claim fails is INVALID.
"""

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


def _with_repeated_study_key() -> str:
    """Return the valid reply with a second study that reuses the key of the first."""
    data = json.loads(valid_response())
    data["studies"].append(dict(data["studies"][0]))
    return json.dumps(data)


CASES = {
    "malformed_json": ('{"studies": [', "response is not JSON"),
    "unfenced_json_in_prose": (
        f"Here is the extraction:\n{valid_response()}\nLet me know if you need more.",
        "response is not JSON",
    ),
    "unknown_top_level_key": (
        json.dumps({**json.loads(valid_response()), "admin": True}),
        "admin: Extra inputs are not permitted",
    ),
    "claims_not_a_list": (
        json.dumps({**json.loads(valid_response()), "claims": "none"}),
        "claims: Input should be a valid tuple",
    ),
    "repeated_study_key": (
        _with_repeated_study_key(),
        "studies.2.key: accuracy appears more than once",
    ),
}

# One claim of three fails the schema or a relationship check. The index is the failing claim.
CLAIM_CASES = {
    "unknown_claim_type": (
        0,
        _edited(0, claim_type="PERFORMANCE_GAIN"),
        "claims.0.claim_type: Input should be",
    ),
    "unknown_field": (
        2,
        _edited(2, offsets=[3, 9]),
        "claims.2.offsets: Extra inputs are not permitted",
    ),
    "unknown_nested_field": (
        1,
        _edited(1, research_context={"training_data": "a corpus"}),
        "claims.1.research_context.training_data: Extra inputs are not permitted",
    ),
    "unknown_study_key": (
        1,
        _edited(1, study_key="latency"),
        "claims.1.study_key: latency is not a study of this output",
    ),
    "source_text_not_found": (
        0,
        _edited(0, evidence={"source_text": "ResNet50 reached 79.1 percent"}),
        "claims.0.evidence.source_text: does not occur in section",
    ),
    "source_text_found_twice": (
        1,
        _edited(1, evidence={"source_text": "images per second"}),
        "claims.1.evidence.source_text: occurs 2 times in section",
    ),
    "span_in_another_document": (
        2,
        _edited(2, evidence={"section_id": "{other}", "source_text": "reached 80.0 percent"}),
        "claims.2.evidence.section_id: {other} is not a section of document",
    ),
}


@pytest.mark.parametrize("case", CASES, ids=CASES)
def test_a_reply_that_fails_as_a_whole_stores_an_invalid_run_and_no_claim(
    corpus: Corpus, case: str
) -> None:
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


@pytest.mark.parametrize("case", CLAIM_CASES, ids=CLAIM_CASES)
def test_a_failing_claim_is_rejected_alone_and_the_rest_are_stored(
    corpus: Corpus, case: str
) -> None:
    other = add_paper(corpus.store, "2409.00002", (OTHER_TEXT,))
    failing, text, expected = CLAIM_CASES[case]
    text = text.replace("{other}", other.sections[0].id)
    expected = expected.replace("{other}", other.sections[0].id)

    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(text),
        normalizer=normalize_claim,
        now=NOW,
    )

    assert run.validation_status is ValidationStatus.PARTIAL
    assert run.raw_response == text
    assert len(run.errors) == 1 and expected in run.errors[0], run.errors
    stored = corpus.store.get_extraction_run(run.id)
    assert stored is not None and stored.errors == run.errors
    # A claim ID is its position in the reply, so the rejected claim leaves a gap.
    assert sorted(
        claim.id for claim in corpus.store.list_claims(research_work_id=corpus.work.id)
    ) == [f"{corpus.document.id}_c{n}" for n in (1, 2, 3) if n != failing + 1]
    assert corpus.store.get_study(f"{corpus.document.id}_accuracy") is not None


def test_a_reply_whose_every_claim_fails_stores_an_invalid_run_and_no_claim(
    corpus: Corpus,
) -> None:
    data = json.loads(valid_response())
    for claim in data["claims"]:
        claim["evidence"]["source_text"] = "text the paper does not hold"
    text = json.dumps(data)

    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(text),
        normalizer=normalize_claim,
        now=NOW,
    )

    assert run.validation_status is ValidationStatus.INVALID
    assert len(run.errors) == 3
    assert corpus.store.list_claims() == []
    assert corpus.store.get_study(f"{corpus.document.id}_accuracy") is None
