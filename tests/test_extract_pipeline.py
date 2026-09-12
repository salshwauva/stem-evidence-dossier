from collections.abc import Iterator

import pytest

from evidence_dossier.extract import PROMPT_VERSION, extract_document
from evidence_dossier.model import ClaimType, ValidationStatus
from evidence_dossier.normalize import normalize_claim
from evidence_dossier.store import Store
from tests.extract_support import MODEL, NOW, Corpus, paper_corpus, valid_response


@pytest.fixture
def corpus() -> Iterator[Corpus]:
    with Store(":memory:") as store:
        yield paper_corpus(store)


def test_valid_reply_stores_the_run_the_studies_and_the_claims(corpus: Corpus) -> None:
    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(valid_response()),
        normalizer=normalize_claim,
        now=NOW,
    )

    assert run.validation_status is ValidationStatus.VALID
    assert run.errors == ()
    assert run.raw_response == valid_response()
    assert corpus.store.get_extraction_run(run.id) == run
    claims = corpus.store.list_claims(research_work_id=corpus.work.id)
    assert [claim.id for claim in claims] == [f"{corpus.document.id}_c{n}" for n in (1, 2, 3)]
    assert {claim.study_id for claim in claims} == {
        f"{corpus.document.id}_accuracy",
        f"{corpus.document.id}_throughput",
    }
    assert all(corpus.store.get_study(claim.study_id) is not None for claim in claims)
    assert [claim.claim_type for claim in claims] == [
        ClaimType.PERFORMANCE,
        ClaimType.PERFORMANCE,
        ClaimType.EFFECT,
    ]


def test_stored_claim_resolves_to_its_source_text_and_its_run(corpus: Corpus) -> None:
    """The increment 3 exit condition from plan section 53."""
    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(valid_response()),
        normalizer=normalize_claim,
        now=NOW,
    )

    for claim in corpus.store.list_claims(research_work_id=corpus.work.id):
        section = corpus.store.get_section(claim.evidence_span.section_id)
        assert section is not None
        assert claim.evidence_span.matches(section)
        assert claim.extraction_run_id == run.id
    stored_run = corpus.store.get_extraction_run(run.id)
    assert stored_run is not None
    assert (stored_run.model_identifier, stored_run.prompt_version, stored_run.schema_version) == (
        MODEL,
        PROMPT_VERSION,
        "core-1",
    )


def test_stored_claims_carry_original_and_canonical_values(corpus: Corpus) -> None:
    extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(valid_response()),
        normalizer=normalize_claim,
        now=NOW,
    )

    first, second, third = corpus.store.list_claims(research_work_id=corpus.work.id)
    assert (first.subject.original, first.subject.canonical) == ("ResNet50", "ResNet-50")
    assert first.measurement is not None and first.measurement.unit is not None
    assert (first.measurement.unit.original, first.measurement.unit.canonical) == ("percent", "%")
    assert first.comparator is not None
    assert first.comparator.name.canonical == "vgg-16 baseline"
    assert second.result.unit is not None
    assert second.result.unit.canonical == "images/s"
    assert third.method is not None
    assert third.method.name.canonical == "label smoothing"
    assert third.research_context.domain is corpus.work.domain


def test_reply_in_a_json_fence_is_accepted(corpus: Corpus) -> None:
    fenced = f"```json\n{valid_response()}\n```"

    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(fenced),
        normalizer=normalize_claim,
        now=NOW,
    )

    assert run.validation_status is ValidationStatus.VALID
    assert run.raw_response == fenced
    assert len(corpus.store.list_claims(research_work_id=corpus.work.id)) == 3


def test_unknown_document_raises(corpus: Corpus) -> None:
    with pytest.raises(LookupError, match="missing_v1"):
        extract_document(
            corpus.store,
            "missing_v1",
            corpus.provider(valid_response()),
            normalizer=normalize_claim,
            now=NOW,
        )
