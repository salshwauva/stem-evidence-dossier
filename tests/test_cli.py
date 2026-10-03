import io
import json
from pathlib import Path
from typing import Any

import pytest

from evidence_dossier.cli import run
from evidence_dossier.extract import ProviderError, ProviderResponse
from evidence_dossier.model import make_document_id, make_section_id, make_work_id
from evidence_dossier.store import Store
from tests.extract_support import RESULTS_TEXT, add_paper, paper_corpus, valid_response
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


def test_extract_prints_a_partial_run_with_the_claims_it_stored(tmp_path: Path) -> None:
    db = tmp_path / "dossier.db"
    with Store(db) as store:
        corpus = paper_corpus(store)
    data = json.loads(valid_response())
    data["claims"][1]["evidence"]["source_text"] = "text the paper does not hold"
    argv = ["--db", str(db), "extract", corpus.document.id, "--model", "unused"]

    status, out, _ = invoke(argv, provider=corpus.provider(json.dumps(data)))

    assert status == 1
    first, second = out.splitlines()
    assert first == f"{corpus.document.id}: PARTIAL, 2 claims"
    assert second.startswith("  claims.1.evidence.source_text: does not occur")


def test_extract_goes_on_after_a_document_with_no_reply(tmp_path: Path) -> None:
    db = tmp_path / "dossier.db"
    with Store(db) as store:
        unknown = add_paper(store, "2409.00002", (RESULTS_TEXT,))
        known = paper_corpus(store)
    argv = ["--db", str(db), "extract", unknown.document.id, known.document.id, "--model", "x"]

    status, out, _ = invoke(argv, provider=known.provider(valid_response()))

    first, second = out.splitlines()
    assert status == 1
    assert first.startswith(
        f"{unknown.document.id}: nothing stored, no reply: no recorded response"
    )
    assert second == f"{known.document.id}: VALID, 3 claims"


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


class FixedReplyProvider:
    """Answers every prompt with one reply, so the demo runs without a model."""

    def __init__(self, text: str) -> None:
        self.text = text

    def complete(self, prompt: str) -> ProviderResponse:
        return ProviderResponse(model_identifier="fixed-model", text=self.text)


def arxiv_fixture_reply() -> str:
    """One valid claim for the invented arXiv fixture. Its passage spans a hard wrap."""
    section_id = make_section_id(make_document_id(make_work_id("arxiv", "9901.00001"), 1), 0)
    return json.dumps(
        {
            "studies": [{"key": "retrieval", "description": "Retrieval on Benchmark X"}],
            "claims": [
                {
                    "study_key": "retrieval",
                    "claim_type": "PERFORMANCE",
                    "claim_text": "With retrieval, the factual error rate fell to 11.5%.",
                    "subject": "retrieval-augmented generation",
                    "predicate": "reduces",
                    "outcome": "factual error rate",
                    "research_context": {"benchmark": "Benchmark X"},
                    "method": {"name": "retrieval-augmented generation"},
                    "comparator": {"name": "same model without retrieval"},
                    "measurement": {"name": "factual error rate", "unit": "percent"},
                    "result": {"direction": "DECREASED", "value": 11.5, "unit": "percent"},
                    "evidence": {
                        "section_id": section_id,
                        "source_text": "the factual error rate fell from 18.2% to 11.5% on Benchmark X",
                    },
                }
            ],
        }
    )


@pytest.fixture
def demo_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "demo"
    folder.mkdir()
    corpus = {
        "note": "An invented corpus for the demo command tests.",
        "works": [{"source": "arxiv", "identifier": "9901.00001"}],
        "queries": [RAG_TEXT],
    }
    (folder / "corpus.json").write_text(json.dumps(corpus))
    return folder


def test_the_demo_records_once_and_replays_the_same_output(tmp_path: Path, demo_dir: Path) -> None:
    recorded_db, replayed_db = tmp_path / "recorded.db", tmp_path / "replayed.db"
    record = ["--db", str(recorded_db), "demo", "--demo-dir", str(demo_dir), "--record"]
    status, recorded, _ = invoke(
        [*record, "--model", "fixed-model"],
        http=RecordedHttpClient(ARXIV_RECORDINGS),
        provider=FixedReplyProvider(arxiv_fixture_reply()),
    )
    assert status == 0
    assert "SUPPORTS (1)" in recorded.splitlines()

    status, replayed, _ = invoke(["--db", str(replayed_db), "demo", "--demo-dir", str(demo_dir)])

    assert status == 0
    assert replayed == recorded.replace(str(recorded_db), str(replayed_db))
    assert replayed.splitlines()[-1].startswith(
        f"Open one claim: evidence-dossier --db {replayed_db}"
    )
    sources = (demo_dir / "SOURCES.md").read_text()
    assert "| arxiv 9901.00001, doi 10.5555/cs.9901.00001 | ABSTRACT_ONLY | CC0 |" in sources


def test_the_demo_refuses_to_reuse_an_existing_store(seeded_db: str, demo_dir: Path) -> None:
    status, out, err = invoke(["--db", seeded_db, "demo", "--demo-dir", str(demo_dir)])

    assert status == 1
    assert out == ""
    assert err.startswith(f"error: {seeded_db} exists")


def test_recording_refuses_to_mix_with_earlier_recordings(tmp_path: Path, demo_dir: Path) -> None:
    (demo_dir / "replies").mkdir()
    (demo_dir / "replies" / "old.json").write_text("{}")
    argv = ["--db", str(tmp_path / "d.db"), "demo", "--demo-dir", str(demo_dir)]

    status, _, err = invoke([*argv, "--record", "--model", "fixed-model"])

    assert status == 1
    assert "holds recordings" in err


def test_a_replay_with_a_missing_reply_names_the_request(tmp_path: Path, demo_dir: Path) -> None:
    status, _, err = invoke(["--db", str(tmp_path / "d.db"), "demo", "--demo-dir", str(demo_dir)])

    assert status == 1
    assert (
        err == f"error: no recorded reply for api/query?id_list=9901.00001 in {demo_dir / 'http'}\n"
    )


def test_a_replay_miss_names_the_document_and_the_fix(tmp_path: Path, demo_dir: Path) -> None:
    record = ["--db", str(tmp_path / "recorded.db"), "demo", "--demo-dir", str(demo_dir)]
    invoke(
        [*record, "--record", "--model", "fixed-model"],
        http=RecordedHttpClient(ARXIV_RECORDINGS),
        provider=FixedReplyProvider(arxiv_fixture_reply()),
    )
    for reply in (demo_dir / "replies").iterdir():
        reply.unlink()
    replay = ["--db", str(tmp_path / "replayed.db"), "demo", "--demo-dir", str(demo_dir)]

    status, out, err = invoke(replay)

    document_id = make_document_id(make_work_id("arxiv", "9901.00001"), 1)
    assert status == 1
    assert f"{document_id}: nothing stored, no reply: no recorded response" in out
    assert f"Query: {RAG_TEXT}" in out.splitlines()
    assert err.startswith("error: 1 document had no recorded reply.")
    assert err.rstrip().endswith("then run demo --record.")


class CountingProvider:
    """Answers every prompt with one reply and counts the calls."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def complete(self, prompt: str) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(model_identifier="fixed-model", text=self.text)


class FailingProvider:
    def complete(self, prompt: str) -> ProviderResponse:
        raise ProviderError("the model call failed")


BOTH_RECORDINGS = {**ARXIV_RECORDINGS, **PUBMED_RECORDINGS}


@pytest.fixture
def two_work_demo(tmp_path: Path, demo_dir: Path) -> Path:
    """A demo folder with one arXiv and one PubMed work, fully recorded."""
    corpus = json.loads((demo_dir / "corpus.json").read_text())
    corpus["works"].append({"source": "pubmed", "identifier": "90001236"})
    (demo_dir / "corpus.json").write_text(json.dumps(corpus))
    status, _, _ = invoke(
        ["--db", str(tmp_path / "all.db"), "demo", "--demo-dir", str(demo_dir)]
        + ["--record", "--model", "fixed-model"],
        http=RecordedHttpClient(BOTH_RECORDINGS),
        provider=FixedReplyProvider(arxiv_fixture_reply()),
    )
    assert status == 0
    return demo_dir


def _snapshot(folder: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in (folder / "replies").iterdir()}


def test_record_only_rerecords_the_named_entry_and_keeps_the_rest(
    tmp_path: Path, two_work_demo: Path
) -> None:
    before = _snapshot(two_work_demo)
    changed = json.loads(arxiv_fixture_reply())
    changed["claims"][0]["claim_text"] += " Recorded again."
    http, provider = RecordedHttpClient(BOTH_RECORDINGS), CountingProvider(json.dumps(changed))
    argv = ["--db", str(tmp_path / "only.db"), "demo", "--demo-dir", str(two_work_demo)]

    status, _, err = invoke(
        [*argv, "--record", "--model", "fixed-model", "--only", "arxiv:9901.00001"],
        http=http,
        provider=provider,
    )

    assert status == 0, err
    assert provider.calls == 1
    assert all(not call.startswith(("entrez", "pmc")) for call in http.calls), http.calls
    after = _snapshot(two_work_demo)
    changed = [name for name in after if before.get(name) != after[name]]
    assert len(changed) == 1
    assert {name: data for name, data in before.items() if name not in changed} == {
        name: data for name, data in after.items() if name not in changed
    }
    status, replayed, err = invoke(
        ["--db", str(tmp_path / "replayed.db"), "demo", "--demo-dir", str(two_work_demo)]
    )
    assert status == 0, err
    assert "Recorded again." in replayed


def test_record_only_names_the_entries_when_one_is_unknown(
    tmp_path: Path, two_work_demo: Path
) -> None:
    http = RecordedHttpClient(BOTH_RECORDINGS)
    db = tmp_path / "only.db"

    status, out, err = invoke(
        ["--db", str(db), "demo", "--demo-dir", str(two_work_demo)]
        + ["--record", "--model", "fixed-model", "--only", "arxiv:0000.00000"],
        http=http,
        provider=FixedReplyProvider("unused"),
    )

    assert status == 1
    assert out == ""
    assert err == (
        "error: --only: no corpus entry arxiv:0000.00000;"
        " entries: arxiv:9901.00001, pubmed:90001236\n"
    )
    assert http.calls == [] and not db.exists()


def test_only_needs_record(tmp_path: Path, two_work_demo: Path) -> None:
    status, _, err = invoke(
        ["--db", str(tmp_path / "d.db"), "demo", "--demo-dir", str(two_work_demo)]
        + ["--only", "arxiv:9901.00001"]
    )

    assert status == 1
    assert err == "error: --only needs --record\n"


def test_record_only_needs_earlier_recordings(tmp_path: Path, demo_dir: Path) -> None:
    status, _, err = invoke(
        ["--db", str(tmp_path / "d.db"), "demo", "--demo-dir", str(demo_dir)]
        + ["--record", "--model", "fixed-model", "--only", "arxiv:9901.00001"]
    )

    assert status == 1
    assert err == f"error: --only needs earlier recordings in {demo_dir}\n"


def test_a_failed_rerecording_keeps_the_old_reply(tmp_path: Path, two_work_demo: Path) -> None:
    before = _snapshot(two_work_demo)

    status, out, err = invoke(
        ["--db", str(tmp_path / "only.db"), "demo", "--demo-dir", str(two_work_demo)]
        + ["--record", "--model", "fixed-model", "--only", "arxiv:9901.00001"],
        http=RecordedHttpClient(BOTH_RECORDINGS),
        provider=FailingProvider(),
    )

    assert status == 1
    assert "nothing stored, no reply: the model call failed" in out
    assert err.startswith("error: 1 document got no reply. A failed recording keeps its earlier")
    assert _snapshot(two_work_demo) == before


def test_record_only_exits_1_when_a_replayed_entry_has_no_reply(
    tmp_path: Path, two_work_demo: Path
) -> None:
    """A change to the prompt makes the other recordings stale, and --only cannot fix that."""
    pubmed_prompt = None
    for reply in (two_work_demo / "replies").iterdir():
        if "reached" not in reply.read_text():  # the PubMed paper holds the second reply
            pubmed_prompt = reply
    assert pubmed_prompt is not None
    pubmed_prompt.unlink()

    status, out, err = invoke(
        ["--db", str(tmp_path / "only.db"), "demo", "--demo-dir", str(two_work_demo)]
        + ["--record", "--model", "fixed-model", "--only", "arxiv:9901.00001"],
        http=RecordedHttpClient(BOTH_RECORDINGS),
        provider=FixedReplyProvider(arxiv_fixture_reply()),
    )

    assert status == 1
    assert "nothing stored, no reply: no recorded response" in out
    assert "then run demo --record without --only." in err


def test_record_only_takes_several_entries(tmp_path: Path, two_work_demo: Path) -> None:
    provider = CountingProvider(arxiv_fixture_reply())

    status, _, err = invoke(
        ["--db", str(tmp_path / "only.db"), "demo", "--demo-dir", str(two_work_demo)]
        + ["--record", "--model", "fixed-model"]
        + ["--only", "arxiv:9901.00001", "--only", "pubmed:90001236"],
        http=RecordedHttpClient(BOTH_RECORDINGS),
        provider=provider,
    )

    assert status == 0, err
    assert provider.calls == 2


def test_the_demo_prints_a_partial_run_and_exits_0(tmp_path: Path, demo_dir: Path) -> None:
    data = json.loads(arxiv_fixture_reply())
    bad = json.loads(json.dumps(data["claims"][0]))
    bad["evidence"]["source_text"] = "text the paper does not hold"
    data["claims"].append(bad)

    status, out, _ = invoke(
        ["--db", str(tmp_path / "d.db"), "demo", "--demo-dir", str(demo_dir)]
        + ["--record", "--model", "fixed-model"],
        http=RecordedHttpClient(ARXIV_RECORDINGS),
        provider=FixedReplyProvider(json.dumps(data)),
    )

    assert status == 0
    assert ": PARTIAL, 1 claims" in out
