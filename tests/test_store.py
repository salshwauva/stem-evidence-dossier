from collections.abc import Iterator
from pathlib import Path

import pytest

from evidence_dossier.model import (
    ClaimType,
    Domain,
    ResearchWork,
    ValidationStatus,
    WorkLink,
    WorkLinkRelation,
    make_work_id,
)
from evidence_dossier.store import ClaimRejectedError, Store
from tests.factories import (
    INVALID_ERRORS,
    INVALID_RAW_RESPONSE,
    Paper,
    biology_paper,
    computer_science_paper,
    invalid_run,
)


@pytest.fixture(params=["memory", "file"])
def store_path(request: pytest.FixtureRequest, tmp_path: Path) -> str | Path:
    if request.param == "memory":
        return ":memory:"
    return tmp_path / "dossier.db"


@pytest.fixture
def store(store_path: str | Path) -> Iterator[Store]:
    with Store(store_path) as opened:
        yield opened


def _add_sources(store: Store, paper: Paper) -> None:
    """Add every record that the claim of the paper depends on, but not the claim."""
    store.add_work(paper.work)
    store.add_source_document(paper.document)
    store.add_section(paper.section)
    store.add_study(paper.study)
    store.add_extraction_run(paper.run)


def _add_paper(store: Store, paper: Paper) -> None:
    _add_sources(store, paper)
    store.add_claim(paper.claim)


def _reopen(store: Store, path: str | Path) -> Store:
    """Reopen a file store from disk, so the reads that follow prove persistence."""
    if path == ":memory:":
        return store
    store.close()
    return Store(path)


def test_every_core_record_round_trips(store_path: str | Path) -> None:
    biology = biology_paper()
    computer_science = computer_science_paper()
    published = ResearchWork(
        id=make_work_id("doi", "10.5555/cs.2401.01234"),
        title=computer_science.work.title,
        domain=Domain.COMPUTER_SCIENCE,
        doi="10.5555/cs.2401.01234",
    )
    link = WorkLink(
        source_work_id=computer_science.work.id,
        relation=WorkLinkRelation.PREPRINT_OF,
        target_work_id=published.id,
    )
    store = Store(store_path)
    _add_paper(store, biology)
    _add_paper(store, computer_science)
    store.add_work(published)
    store.add_work_link(link)

    store = _reopen(store, store_path)

    for paper in (biology, computer_science):
        assert store.get_work(paper.work.id) == paper.work
        assert store.get_source_document(paper.document.id) == paper.document
        assert store.get_section(paper.section.id) == paper.section
        assert store.get_study(paper.study.id) == paper.study
        assert store.get_extraction_run(paper.run.id) == paper.run
        assert store.get_claim(paper.claim.id) == paper.claim
    assert store.get_work(published.id) == published
    assert store.get_work_links(computer_science.work.id) == [link]
    assert store.get_work_links(published.id) == [link]
    store.close()


def test_get_returns_none_for_an_unknown_id(store: Store) -> None:
    assert store.get_work("missing") is None
    assert store.get_source_document("missing") is None
    assert store.get_section("missing") is None
    assert store.get_study("missing") is None
    assert store.get_claim("missing") is None
    assert store.get_extraction_run("missing") is None
    assert store.get_work_links("missing") == []


def test_invalid_extraction_run_keeps_its_raw_response_and_errors(store_path: str | Path) -> None:
    paper = biology_paper()
    run = invalid_run(paper.document.id)
    store = Store(store_path)
    store.add_work(paper.work)
    store.add_source_document(paper.document)
    store.add_extraction_run(run)

    store = _reopen(store, store_path)
    stored = store.get_extraction_run(run.id)

    assert stored == run
    assert stored is not None
    assert stored.validation_status is ValidationStatus.INVALID
    assert stored.raw_response == INVALID_RAW_RESPONSE
    assert stored.errors == INVALID_ERRORS
    store.close()


def test_add_claim_refuses_a_span_that_does_not_match_the_section_text(store: Store) -> None:
    paper = biology_paper()
    _add_sources(store, paper)
    span = paper.claim.evidence_span
    shifted = span.model_copy(
        update={"start_offset": span.start_offset + 1, "end_offset": span.end_offset + 1}
    )

    with pytest.raises(ClaimRejectedError, match="does not match the section text"):
        store.add_claim(paper.claim.model_copy(update={"evidence_span": shifted}))

    assert store.get_claim(paper.claim.id) is None


def test_add_claim_refuses_a_study_from_another_work(store: Store) -> None:
    paper = biology_paper()
    other = biology_paper(pmid="87654321")
    _add_sources(store, paper)
    _add_sources(store, other)

    with pytest.raises(ClaimRejectedError, match="study .* belongs to research work"):
        store.add_claim(paper.claim.model_copy(update={"study_id": other.study.id}))

    assert store.list_claims() == []


def test_add_claim_refuses_a_section_from_another_work(store: Store) -> None:
    paper = biology_paper()
    other = biology_paper(pmid="87654321")
    _add_sources(store, paper)
    _add_sources(store, other)
    # Both sections hold the same text, so only the owning work differs.
    span = paper.claim.evidence_span.model_copy(update={"section_id": other.section.id})

    with pytest.raises(ClaimRejectedError, match="section .* belongs to research work"):
        store.add_claim(paper.claim.model_copy(update={"evidence_span": span}))

    assert store.list_claims() == []


def test_add_claim_refuses_a_span_that_names_another_work(store: Store) -> None:
    paper = biology_paper()
    other = biology_paper(pmid="87654321")
    _add_sources(store, paper)
    _add_sources(store, other)
    span = paper.claim.evidence_span.model_copy(update={"research_work_id": other.work.id})

    with pytest.raises(ClaimRejectedError, match="span names research work"):
        store.add_claim(paper.claim.model_copy(update={"evidence_span": span}))

    assert store.list_claims() == []


@pytest.mark.parametrize("missing", ["study", "section"])
def test_add_claim_refuses_a_claim_whose_study_or_section_is_missing(
    store: Store, missing: str
) -> None:
    paper = biology_paper()
    _add_sources(store, paper)
    if missing == "study":
        claim = paper.claim.model_copy(update={"study_id": "study-missing"})
    else:
        span = paper.claim.evidence_span.model_copy(update={"section_id": "section-missing"})
        claim = paper.claim.model_copy(update={"evidence_span": span})

    with pytest.raises(ClaimRejectedError, match="is not in the store"):
        store.add_claim(claim)

    assert store.list_claims() == []


def test_list_claims_filters_by_domain_claim_type_work_and_study(store: Store) -> None:
    biology = biology_paper()
    computer_science = computer_science_paper()
    _add_paper(store, biology)
    _add_paper(store, computer_science)

    # Claims come back ordered by ID: "claim-12345678" sorts before "claim-2401.01234".
    assert store.list_claims() == [biology.claim, computer_science.claim]
    assert store.list_claims(domain=Domain.BIOLOGY) == [biology.claim]
    assert store.list_claims(claim_type=ClaimType.PERFORMANCE) == [computer_science.claim]
    assert store.list_claims(research_work_id=biology.work.id) == [biology.claim]
    assert store.list_claims(study_id=computer_science.study.id) == [computer_science.claim]
    assert store.list_claims(domain=Domain.BIOLOGY, claim_type=ClaimType.PERFORMANCE) == []
