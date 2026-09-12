import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from evidence_dossier.model import Domain
from evidence_dossier.query import Retriever, parse_query
from evidence_dossier.store import Store
from tests.query_corpus import retrieval_papers, seed
from tests.test_query_parser import MAPT_TEXT, RAG_TEXT

BENCHMARK = Path(__file__).parent / "fixtures" / "query" / "benchmark.json"


@pytest.fixture
def store() -> Iterator[Store]:
    with Store(":memory:") as opened:
        seed(opened, retrieval_papers())
        yield opened


def _ids(store: Store, text: str, *, domain: Domain | None = None, limit: int = 20) -> list[str]:
    candidates = Retriever(store).retrieve(parse_query(text, domain=domain), limit=limit)
    return [candidate.claim.id for candidate in candidates]


def test_the_rag_proposition_retrieves_the_computer_science_claim_first(store: Store) -> None:
    candidates = Retriever(store).retrieve(parse_query(RAG_TEXT), limit=5)

    assert candidates[0].claim.id == "claim-9901.00001"
    assert "retrieval" in candidates[0].matched_terms
    assert "hallucination" not in candidates[0].matched_terms


def test_a_biology_proposition_retrieves_the_biology_claim(store: Store) -> None:
    assert _ids(store, MAPT_TEXT)[0] == "claim-12345678"


def test_a_nonsense_proposition_retrieves_nothing(store: Store) -> None:
    assert _ids(store, "quantum foam warps spacetime") == []


def test_a_domain_filter_excludes_the_other_domain(store: Store) -> None:
    assert _ids(store, RAG_TEXT, domain=Domain.BIOLOGY) == []
    assert _ids(store, MAPT_TEXT, domain=Domain.COMPUTER_SCIENCE) == []
    assert _ids(store, MAPT_TEXT, domain=Domain.BIOLOGY) == ["claim-12345678"]


def test_the_limit_bounds_the_candidates(store: Store) -> None:
    # "against" appears in several invented passages, so more than one claim matches.
    assert len(_ids(store, "retrieval against caching", limit=1)) == 1


def test_recall_at_five_over_the_query_benchmark_is_one(store: Store) -> None:
    cases = json.loads(BENCHMARK.read_text(encoding="utf-8"))["cases"]
    recalls = []
    for case in cases:
        domain = None if case["domain"] is None else Domain(case["domain"])
        top = set(_ids(store, case["text"], domain=domain, limit=5))
        relevant = set(case["relevant_claim_ids"])
        recalls.append(len(top & relevant) / len(relevant))

    assert len(cases) == 6
    assert sum(recalls) / len(recalls) == 1.0
