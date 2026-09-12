from datetime import date

import pytest

from evidence_dossier.ingest import ArxivAdapter, PubMedAdapter
from evidence_dossier.model import Author, Domain, SourceLevel, make_work_id
from tests.recorded_http import ARXIV_RECORDINGS, PUBMED_RECORDINGS, RecordedHttpClient


def test_pubmed_search_returns_pmids_in_source_order() -> None:
    adapter = PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS))
    hits = adapter.search("MAPT knockdown", limit=5)
    assert [hit.identifier for hit in hits] == ["90001234", "90001235"]
    assert {hit.source for hit in hits} == {"pubmed"}


def test_pubmed_metadata_parses_the_article_record() -> None:
    adapter = PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS))
    work = adapter.fetch_metadata("90001234")
    assert work.id == make_work_id("pmid", "90001234")
    assert work.title == "MAPT knockdown and neuronal survival in a test dementia model"
    assert work.domain == Domain.BIOLOGY
    assert work.doi == "10.5555/bio.90001234"
    assert work.abstract is not None
    assert work.abstract.startswith("Tau accumulation is a feature")
    assert "raised neuronal survival by 32%" in work.abstract
    assert work.publication_date == date(2025, 3, 14)
    assert work.venue == "Journal of Test Neuroscience"
    assert work.authors == (
        Author(
            name="Ana Rivera", affiliations=("Neurodegeneration Lab, Test University, Testville.",)
        ),
        Author(
            name="Bem Okafor",
            affiliations=(
                "Neurodegeneration Lab, Test University, Testville.",
                "Test Institute, Testville.",
            ),
        ),
    )
    assert work.external_identifiers == {
        "pmid": "90001234",
        "doi": "10.5555/bio.90001234",
        "pmc": "PMC9900001",
    }


def test_pubmed_metadata_reads_a_month_name_and_no_day() -> None:
    work = PubMedAdapter(RecordedHttpClient(PUBMED_RECORDINGS)).fetch_metadata("90001235")
    assert work.publication_date == date(2024, 11, 1)
    assert work.doi is None
    assert work.authors == (Author(name="Lina Haddad"),)


def test_pubmed_full_text_comes_from_pmc_as_jats() -> None:
    http = RecordedHttpClient(PUBMED_RECORDINGS)
    fetched = PubMedAdapter(http).fetch_full_text("90001234")
    assert fetched is not None
    assert fetched.source_level == SourceLevel.FULL_TEXT
    assert fetched.source_format == "jats_xml"
    assert "<article-title>MAPT knockdown" in fetched.text
    assert http.calls == [
        "pmc/utils/idconv/v1.0?ids=90001234",
        "entrez/eutils/efetch.fcgi?db=pmc&id=PMC9900001",
    ]


def test_pubmed_full_text_is_none_when_pmc_has_no_record() -> None:
    http = RecordedHttpClient(PUBMED_RECORDINGS)
    assert PubMedAdapter(http).fetch_full_text("90001235") is None
    assert http.calls == ["pmc/utils/idconv/v1.0?ids=90001235"]


def test_arxiv_search_strips_the_version_from_each_identifier() -> None:
    hits = ArxivAdapter(RecordedHttpClient(ARXIV_RECORDINGS)).search(
        "retrieval factual errors", limit=2
    )
    assert [(hit.identifier, hit.title) for hit in hits] == [
        ("2401.01234", "Retrieval and factual errors in a test language model"),
        ("2402.05678", "Rerankers and hallucination on a test benchmark"),
    ]


def test_arxiv_metadata_parses_the_atom_entry() -> None:
    work = ArxivAdapter(RecordedHttpClient(ARXIV_RECORDINGS)).fetch_metadata("2401.01234")
    assert work.id == make_work_id("arxiv", "2401.01234")
    assert work.title == "Retrieval and factual errors in a test language model"
    assert work.domain == Domain.COMPUTER_SCIENCE
    assert work.doi == "10.5555/cs.2401.01234"
    assert work.publication_date == date(2024, 1, 5)
    assert work.venue == "Proceedings of the Test Language Conference 2024"
    assert work.authors == (
        Author(name="C. Lindqvist", affiliations=("Test Systems Group",)),
        Author(name="E. Novak"),
    )
    assert work.external_identifiers == {"arxiv": "2401.01234", "doi": "10.5555/cs.2401.01234"}


def test_arxiv_full_text_is_the_abstract_with_its_inner_newlines() -> None:
    fetched = ArxivAdapter(RecordedHttpClient(ARXIV_RECORDINGS)).fetch_full_text("2401.01234")
    assert fetched is not None
    assert fetched.source_level == SourceLevel.ABSTRACT_ONLY
    assert fetched.source_format == "plain_text"
    assert fetched.text == (
        "With retrieval, the factual error rate fell from 18.2% to 11.5% on\n"
        "Benchmark X. The gain held across three seeds."
    )


def test_arxiv_unknown_identifier_raises_lookup_error() -> None:
    with pytest.raises(LookupError):
        ArxivAdapter(RecordedHttpClient(ARXIV_RECORDINGS)).fetch_metadata("9999.99999")


def test_a_request_without_a_recording_fails_instead_of_going_live() -> None:
    with pytest.raises(KeyError):
        ArxivAdapter(RecordedHttpClient({})).fetch_metadata("2401.01234")
