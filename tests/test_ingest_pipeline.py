from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from evidence_dossier.ingest import ArxivAdapter, PubMedAdapter, ingest_work
from evidence_dossier.model import SectionType, SourceLevel, make_document_id, make_work_id
from evidence_dossier.store import Store
from tests.recorded_http import (
    ARXIV_RECORDINGS,
    FIXTURES_DIR,
    PUBMED_RECORDINGS,
    RecordedHttpClient,
)

FETCHED_AT = datetime(2026, 9, 12, 8, 30, tzinfo=UTC)


@pytest.fixture
def store() -> Iterator[Store]:
    with Store(":memory:") as opened:
        yield opened


def test_full_text_ingestion_stores_the_work_document_and_sections(store: Store) -> None:
    result = ingest_work(
        store,
        PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS)),
        "90001234",
        fetched_at=FETCHED_AT,
    )
    assert result.work_id == make_work_id("pmid", "90001234")
    assert result.document_id == make_document_id(result.work_id, 1)
    assert result.version == 1
    assert result.source_level == SourceLevel.FULL_TEXT
    assert result.section_count == 10
    assert result.stored is True
    work = store.get_work(result.work_id)
    assert work is not None
    assert work.title == "MAPT knockdown and neuronal survival in a test dementia model"
    document = store.get_source_document(result.document_id)
    assert document is not None
    assert document.source_format == "jats_xml"
    assert document.fetched_at == FETCHED_AT
    assert document.raw_text == (FIXTURES_DIR / "pmc_efetch_PMC99900001.xml").read_text()


def test_a_fixture_passage_sits_at_the_same_offsets_in_the_stored_section(store: Store) -> None:
    passage = "raised neuronal survival by 32% relative to a scrambled control (p < 0.01)"
    result = ingest_work(
        store,
        PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS)),
        "90001234",
        fetched_at=FETCHED_AT,
    )
    results = store.get_section(f"{result.document_id}_s4")
    assert results is not None
    assert results.section_type == SectionType.RESULTS
    start = results.text.index(passage)
    end = start + len(passage)
    reloaded = store.get_section(results.id)
    assert reloaded is not None
    assert reloaded.text[start:end] == passage


def test_abstract_fallback_when_pmc_returns_nothing(store: Store) -> None:
    http = RecordedHttpClient(PUBMED_RECORDINGS)
    result = ingest_work(store, PubMedAdapter(http), "90001235", fetched_at=FETCHED_AT)
    assert result.source_level == SourceLevel.ABSTRACT_ONLY
    assert result.section_count == 1
    section = store.get_section(f"{result.document_id}_s0")
    assert section is not None
    assert section.section_type == SectionType.ABSTRACT
    assert section.text.startswith("MAPT knockdown lowered phosphorylated tau by 41%")
    assert "entrez/eutils/efetch.fcgi?db=pmc&id=PMC99900001" not in http.calls


def test_arxiv_ingestion_is_abstract_only(store: Store) -> None:
    result = ingest_work(
        store,
        ArxivAdapter(RecordedHttpClient(ARXIV_RECORDINGS)),
        "9901.00001",
        fetched_at=FETCHED_AT,
    )
    assert result.work_id == make_work_id("arxiv", "9901.00001")
    assert result.source_level == SourceLevel.ABSTRACT_ONLY
    assert result.section_count == 1


def test_metadata_only_when_the_source_has_no_abstract(store: Store) -> None:
    class NoTextAdapter(ArxivAdapter):
        def fetch_full_text(self, identifier: str) -> None:
            return None

    adapter = NoTextAdapter(RecordedHttpClient(ARXIV_RECORDINGS))
    work = adapter.fetch_metadata("9901.00001").model_copy(update={"abstract": None})
    adapter.fetch_metadata = lambda identifier: work  # type: ignore[method-assign]
    result = ingest_work(store, adapter, "9901.00001", fetched_at=FETCHED_AT)
    assert result.source_level == SourceLevel.METADATA_ONLY
    assert result.section_count == 0
    document = store.get_source_document(result.document_id)
    assert document is not None
    assert document.raw_text == ""


def test_second_ingestion_of_the_same_text_writes_nothing(store: Store) -> None:
    adapter = PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS))
    first = ingest_work(store, adapter, "90001234", fetched_at=FETCHED_AT)
    second = ingest_work(store, adapter, "90001234", fetched_at=datetime(2026, 9, 13, tzinfo=UTC))
    assert second == first.model_copy(update={"stored": False})
    assert store.get_source_document(make_document_id(first.work_id, 2)) is None
    document = store.get_source_document(first.document_id)
    assert document is not None
    assert document.fetched_at == FETCHED_AT


def test_changed_text_writes_version_two(store: Store) -> None:
    adapter = PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS))
    first = ingest_work(store, adapter, "90001234", fetched_at=FETCHED_AT)
    changed = dict(PUBMED_RECORDINGS)
    changed["pmc/utils/idconv/v1.0?ids=90001234"] = "pmc_idconv_90001235.json"
    second = ingest_work(
        store, PubMedAdapter(RecordedHttpClient(changed)), "90001234", fetched_at=FETCHED_AT
    )
    assert second.version == 2
    assert second.document_id == make_document_id(first.work_id, 2)
    assert second.source_level == SourceLevel.ABSTRACT_ONLY
    assert second.stored is True
    assert store.get_source_document(first.document_id) is not None
    assert store.get_section(f"{first.document_id}_s4") is not None
