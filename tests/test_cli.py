import io
from pathlib import Path
from typing import Any

import pytest

from evidence_dossier.cli import run
from evidence_dossier.model import make_document_id, make_work_id
from evidence_dossier.query import ModelQueryExpander
from evidence_dossier.store import Store
from tests.extract_support import paper_corpus, valid_response
from tests.query_corpus import retrieval_papers, seed
from tests.recorded_http import ARXIV_RECORDINGS, PUBMED_RECORDINGS, RecordedHttpClient
from tests.test_query_parser import RAG_TEXT


def invoke(argv: list[str], **services: Any) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    status = run(argv, out=out, err=err, **services)
    return status, out.getvalue(), err.getvalue()


@pytest.fixture
def seeded_db(tmp_path: Path) -> str:
    path = tmp_path / "dossier.db"
    with Store(path) as store:
        seed(store, retrieval_papers())
    return str(path)


def test_ingest_prints_the_work_and_stores_its_text(tmp_path: Path) -> None:
    db = str(tmp_path / "dossier.db")
    http = RecordedHttpClient(PUBMED_RECORDINGS)

    status, out, _ = invoke(["--db", db, "ingest", "pubmed", "90001234"], http=http)

    work_id = make_work_id("pmid", "90001234")
    assert status == 0
    assert out.splitlines() == [
        "pubmed 90001234: MAPT knockdown and neuronal survival in a test dementia model",
        f"  {make_document_id(work_id, 1)}, FULL_TEXT, 10 sections, stored, license CC BY",
    ]
    with Store(db) as store:
        assert store.get_work(work_id) is not None


def test_ingest_reports_an_unknown_identifier(tmp_path: Path) -> None:
    db = str(tmp_path / "dossier.db")
    http = RecordedHttpClient(ARXIV_RECORDINGS)

    status, out, err = invoke(["--db", db, "ingest", "arxiv", "9999.99999"], http=http)

    assert status == 1
    assert out == ""
    assert err == "error: arXiv has no entry with identifier 9999.99999\n"


def test_extract_prints_the_run_status_and_the_claim_count(tmp_path: Path) -> None:
    db = tmp_path / "dossier.db"
    with Store(db) as store:
        corpus = paper_corpus(store)
    argv = ["--db", str(db), "extract", corpus.document.id, "--model", "unused"]

    status, out, _ = invoke(argv, provider=corpus.provider(valid_response()))

    assert status == 0
    assert out == f"{corpus.document.id}: VALID, 3 claims\n"


def test_extract_prints_the_errors_of_an_invalid_reply(tmp_path: Path) -> None:
    db = tmp_path / "dossier.db"
    with Store(db) as store:
        corpus = paper_corpus(store)
    argv = ["--db", str(db), "extract", corpus.document.id, "--model", "unused"]

    status, out, _ = invoke(argv, provider=corpus.provider("not json"))

    assert status == 1
    first, second = out.splitlines()
    assert first == f"{corpus.document.id}: INVALID, 0 claims"
    assert second.startswith("  response is not JSON")


def test_search_prints_each_stance_group_with_its_reasons_and_passage(seeded_db: str) -> None:
    status, out, _ = invoke(["--db", seeded_db, "search", RAG_TEXT, "--limit", "5"])

    lines = out.splitlines()
    assert status == 0
    assert lines[0] == f"Query: {RAG_TEXT}"
    assert lines[1].startswith('Parsed: subject "retrieval-augmented generation"')
    assert "SUPPORTS (1)" in lines
    assert (
        "  claim-9901.00001  Retrieval and factual errors in a test language model (2024)" in lines
    )
    assert "    Comparability: EXACT" in lines
    assert '    Passage: RESULTS "Results", characters 16 to 63' in lines
    assert '      "the factual error rate fell from 18.2% to 11.5%"' in lines
    assert lines[-1] == "No claims: CONTRADICTS, MIXED, NULL, INDIRECT, INSUFFICIENTLY_COMPARABLE"


def test_search_with_an_expander_reaches_a_claim_that_the_query_words_miss(seeded_db: str) -> None:
    text = "quantum foam warps spacetime"
    _, plain, _ = invoke(["--db", seeded_db, "search", text])
    expander = ModelQueryExpander(lambda prompt: '{"terms": ["MAPT knockdown"]}')

    status, out, _ = invoke(["--db", seeded_db, "search", text], expander=expander)

    assert status == 0
    assert "claim-90000001" not in plain
    assert "claim-90000001" in out


def test_claim_prints_the_context_baseline_metric_result_and_passage(seeded_db: str) -> None:
    status, out, _ = invoke(["--db", seeded_db, "claim", "claim-9901.00001"])

    lines = out.splitlines()
    assert status == 0
    assert lines[0] == "Claim claim-9901.00001 (PERFORMANCE)"
    assert "Baseline: no retrieval (canonical: same model without retrieval)" in lines
    assert "Metric: factual error rate (%)" in lines
    assert lines[lines.index('Passage: RESULTS "Results", characters 16 to 63') + 1] == (
        '  "the factual error rate fell from 18.2% to 11.5%"'
    )
    assert lines[-1].startswith("Extraction: run run-9901.00001, model extractor-model-a")


def test_claim_reports_a_missing_claim(seeded_db: str) -> None:
    status, out, err = invoke(["--db", seeded_db, "claim", "claim-missing"])

    assert status == 1
    assert out == ""
    assert err == "error: claim claim-missing is not in the store\n"


def test_a_second_extract_of_a_document_reports_it_and_stores_nothing(tmp_path: Path) -> None:
    db = tmp_path / "dossier.db"
    with Store(db) as store:
        corpus = paper_corpus(store)
    argv = ["--db", str(db), "extract", corpus.document.id, "--model", "unused"]
    invoke(argv, provider=corpus.provider(valid_response()))

    status, out, _ = invoke(argv, provider=corpus.provider(valid_response() + "\n"))

    assert status == 1
    assert out.splitlines()[0] == (
        f"{corpus.document.id}: nothing stored, an earlier extraction holds its IDs"
    )


def test_claim_without_an_outcome_leaves_the_outcome_out(tmp_path: Path) -> None:
    db = tmp_path / "dossier.db"
    papers = retrieval_papers()
    bare = papers[0].claim.model_copy(update={"id": "claim-no-outcome", "outcome": None})
    with Store(db) as store:
        seed(store, papers, extra_claims=[bare])

    status, out, _ = invoke(["--db", str(db), "claim", "claim-no-outcome"])

    assert status == 0
    predicate = [line for line in out.splitlines() if line.startswith("Predicate:")]
    assert predicate == [f"Predicate: {bare.predicate}"]
