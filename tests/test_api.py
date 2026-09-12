from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from evidence_dossier.api import create_app
from evidence_dossier.query import STANCE_ORDER
from evidence_dossier.store import Store
from tests.evaluate_corpus import dev_dataset
from tests.evaluate_corpus import seed as seed_gold
from tests.evaluate_predictions import FIXTURE_DIR
from tests.query_corpus import retrieval_papers, seed
from tests.test_query_parser import RAG_TEXT


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "dossier.db"
    with Store(path) as store:
        seed(store, retrieval_papers())
    return path


@pytest.fixture
def client(db_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(db_path)) as opened:
        yield opened


@pytest.fixture
def evaluation_client(tmp_path: Path) -> Iterator[TestClient]:
    """A client whose store holds the gold works, next to the gold directory itself."""
    path = tmp_path / "evaluation.db"
    with Store(path) as store:
        seed(store, retrieval_papers())
        seed_gold(store, dev_dataset())
    with TestClient(create_app(path, gold_dir=FIXTURE_DIR)) as opened:
        yield opened


def test_search_returns_groups_in_the_plan_order_with_matching_provenance(
    client: TestClient, db_path: Path
) -> None:
    response = client.post("/search/evidence", json={"text": RAG_TEXT, "limit": 5})

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert [group["stance"] for group in body["groups"]] == [
        stance.value for stance in STANCE_ORDER
    ]
    assert body["proposition"]["subject"] == "retrieval-augmented generation"
    assert body["candidates"][0]["claim"]["id"] == "claim-9901.00001"
    supports = body["groups"][0]["items"]
    assert [item["claim"]["id"] for item in supports] == ["claim-9901.00001"]
    provenance = supports[0]["provenance"]
    with Store(db_path) as store:
        section = store.get_section(provenance["section_id"])
    assert section is not None
    assert (
        section.text[provenance["start_offset"] : provenance["end_offset"]]
        == provenance["source_text"]
    )
    assert supports[0]["stance_reason"]
    assert len(supports[0]["comparability_reasons"]) == 7


def test_dossier_create_and_get_round_trip(client: TestClient) -> None:
    created = client.post("/dossiers", json={"text": RAG_TEXT})
    assert created.status_code == 201
    dossier = created.json()["dossier"]
    assert dossier["counts"]["claims"] == 1
    assert dossier["counts"]["studies"] == 1
    assert dossier["counts"]["works"] == 1
    assert dossier["counts"]["by_stance"]["SUPPORTS"] == 1
    assert dossier["corpus_scope"]["claim_count"] == 6
    assert dossier["corpus_scope"]["source_levels"] == ["ABSTRACT_ONLY", "FULL_TEXT"]

    fetched = client.get(f"/dossiers/{dossier['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["dossier"] == dossier
    assert fetched.json()["proposition"]["id"] == dossier["query_id"]
    assert [a["claim_id"] for a in fetched.json()["assessments"]] == ["claim-9901.00001"]


def test_claim_and_work_routes_expose_the_records(client: TestClient) -> None:
    claim = client.get("/claims/claim-9901.00001")
    assert claim.status_code == 200
    work = client.get(f"/works/{claim.json()['research_work_id']}")

    assert work.status_code == 200
    assert work.json()["claim_ids"] == ["claim-9901.00001"]
    assert work.json()["links"] == []


@pytest.mark.parametrize("path", ["/claims/missing", "/works/missing", "/dossiers/missing"])
def test_unknown_ids_give_404(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("limit", [0, 101])
def test_the_limit_is_bounded(client: TestClient, limit: int) -> None:
    assert (
        client.post("/search/evidence", json={"text": RAG_TEXT, "limit": limit}).status_code == 422
    )


def test_conflicts_is_still_a_placeholder(client: TestClient) -> None:
    conflicts = client.get("/conflicts")

    assert conflicts.status_code == 200
    assert conflicts.json()["conflicts"] == []


def test_evaluation_without_a_gold_directory_gives_404(client: TestClient) -> None:
    response = client.get("/evaluation")

    assert response.status_code == 404
    assert response.json()["detail"] == "no gold directory is configured for this app"


def test_evaluation_scores_the_store_against_the_gold_directory(
    evaluation_client: TestClient,
) -> None:
    response = evaluation_client.get("/evaluation")

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["split"] == "dev"
    assert body["markdown"].startswith("# Evaluation report")
    assert body["model_identifier"] == "extractor-model-a"
    assert body["extraction"]["fields"]["micro"]["f1"] == 1.0
    assert body["retrieval"]["per_query"][0]["query_id"] == "q1"
    assert body["stance"]["labeled"] == 9
    assert body["notes"] == []


def test_the_test_split_reads_the_same_directory(evaluation_client: TestClient) -> None:
    """load_dataset takes the split as a label, not as a subdirectory (plan section 49).

    A gold directory without a test split therefore scores its files again
    under the name "test". A per-split directory is the caller's job.
    """
    response = evaluation_client.get("/evaluation", params={"split": "test"})

    assert response.status_code == 200
    assert response.json()["split"] == "test"
    assert response.json()["extraction"]["fields"]["micro"]["f1"] == 1.0


def test_an_unknown_split_gives_422(evaluation_client: TestClient) -> None:
    assert evaluation_client.get("/evaluation", params={"split": "holdout"}).status_code == 422
