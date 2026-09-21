import xml.etree.ElementTree as ET
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime

import pytest

from evidence_dossier.ingest import ArxivAdapter, FetchedText, PubMedAdapter, ingest_work
from evidence_dossier.ingest.pubmed import CLOUD_URL
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


class CloudDownClient(RecordedHttpClient):
    """Serves the recordings, except that every call to the PMC cloud bucket fails."""

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        if url.startswith(CLOUD_URL):
            raise ConnectionError("cloud bucket unavailable")
        return super().get(url, params)


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
    assert result.license == "CC BY"
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


def test_abstract_fallback_for_a_noncommercial_license(store: Store) -> None:
    http = RecordedHttpClient(PUBMED_RECORDINGS)
    result = ingest_work(store, PubMedAdapter(http), "90001236", fetched_at=FETCHED_AT)
    assert result.source_level == SourceLevel.ABSTRACT_ONLY
    assert result.section_count == 1
    assert result.license is None
    section = store.get_section(f"{result.document_id}_s0")
    assert section is not None
    assert section.section_type == SectionType.ABSTRACT
    assert section.text.startswith("MAPT knockdown lowered phosphorylated tau by 27%")
    assert "entrez/eutils/efetch.fcgi?db=pmc&id=PMC99900002" not in http.calls


def test_abstract_fallback_when_the_cloud_lists_no_version(store: Store) -> None:
    http = RecordedHttpClient(PUBMED_RECORDINGS)
    result = ingest_work(store, PubMedAdapter(http), "90001237", fetched_at=FETCHED_AT)
    assert result.source_level == SourceLevel.ABSTRACT_ONLY
    assert result.license is None
    assert "entrez/eutils/efetch.fcgi?db=pmc&id=PMC99900003" not in http.calls


def test_abstract_fallback_when_the_full_text_fetch_raises(store: Store) -> None:
    result = ingest_work(
        store,
        PubMedAdapter(CloudDownClient(PUBMED_RECORDINGS)),
        "90001234",
        fetched_at=FETCHED_AT,
    )
    assert result.source_level == SourceLevel.ABSTRACT_ONLY
    assert result.stored is True
    assert result.license is None
    assert result.fetch_error == "ConnectionError: cloud bucket unavailable"
    section = store.get_section(f"{result.document_id}_s0")
    assert section is not None
    assert section.section_type == SectionType.ABSTRACT


def test_a_failed_fetch_keeps_the_stored_full_text(store: Store) -> None:
    first = ingest_work(
        store,
        PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS)),
        "90001234",
        fetched_at=FETCHED_AT,
    )
    second = ingest_work(
        store,
        PubMedAdapter(CloudDownClient(PUBMED_RECORDINGS)),
        "90001234",
        fetched_at=FETCHED_AT,
    )
    assert second.document_id == first.document_id
    assert second.version == 1
    assert second.source_level == SourceLevel.FULL_TEXT
    assert second.stored is False
    assert second.fetch_error == "ConnectionError: cloud bucket unavailable"
    assert store.get_source_document(make_document_id(first.work_id, 2)) is None


def test_a_failed_fetch_still_versions_a_changed_abstract(store: Store) -> None:
    """The keep rule covers a downgrade only. A new abstract at the same level is stored."""
    first = ingest_work(
        store,
        PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS)),
        "90001237",
        fetched_at=FETCHED_AT,
    )
    assert first.source_level == SourceLevel.ABSTRACT_ONLY
    changed = dict(PUBMED_RECORDINGS)
    changed["entrez/eutils/efetch.fcgi?db=pubmed&id=90001237"] = "pubmed_efetch_90001236.xml"
    second = ingest_work(
        store,
        PubMedAdapter(CloudDownClient(changed)),
        "90001237",
        fetched_at=FETCHED_AT,
    )
    assert second.version == 2
    assert second.stored is True
    assert second.source_level == SourceLevel.ABSTRACT_ONLY
    assert second.fetch_error == "ConnectionError: cloud bucket unavailable"
    section = store.get_section(f"{second.document_id}_s0")
    assert section is not None
    assert section.text.startswith("MAPT knockdown lowered phosphorylated tau by 27%")


def test_a_section_parse_error_leaves_no_work_behind(store: Store) -> None:
    class BrokenXmlAdapter(ArxivAdapter):
        def fetch_full_text(self, identifier: str) -> FetchedText:
            return FetchedText(
                text="<article><body>", source_level=SourceLevel.FULL_TEXT, source_format="jats_xml"
            )

    adapter = BrokenXmlAdapter(RecordedHttpClient(ARXIV_RECORDINGS))
    with pytest.raises(ET.ParseError):
        ingest_work(store, adapter, "9901.00001", fetched_at=FETCHED_AT)
    assert store.get_work(make_work_id("arxiv", "9901.00001")) is None


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
