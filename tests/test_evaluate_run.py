"""evaluate_store scores the stored claims and the search results of one store.

The store holds the gold claims under invented IDs, so a run that scores 1.0
proves that the span match, not an ID convention, maps a stored claim onto its
gold key.
"""

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime

import pytest

from evidence_dossier.evaluate import Dataset, EvaluationReport, SearchHit, evaluate_store
from evidence_dossier.model import ComparabilityLevel, Stance, Term
from evidence_dossier.store import Store
from tests.evaluate_corpus import dev_dataset, seed, stored_claim_id, study_id

NOW = datetime(2026, 9, 12, 6, 0, tzinfo=UTC)
B1, C1 = "work_bio_0001", "work_cs_0001"
ABSENT = "stored-claim-absent"


class FixedSearch:
    """A search that answers every query with the same ranking, and records the query text."""

    def __init__(self, claim_ids: Sequence[str]) -> None:
        self.claim_ids = tuple(claim_ids)
        self.queries: list[str] = []

    def __call__(self, store: Store, query_text: str) -> Sequence[SearchHit]:
        self.queries.append(query_text)
        return [
            SearchHit(
                claim_id=claim_id,
                stance=Stance.SUPPORTS,
                comparability=ComparabilityLevel.HIGH,
                reason="fixed test search",
            )
            for claim_id in self.claim_ids
        ]


@pytest.fixture
def dataset() -> Dataset:
    return dev_dataset()


@pytest.fixture
def store(dataset: Dataset) -> Iterator[Store]:
    with Store(":memory:") as opened:
        seed(opened, dataset)
        yield opened


def _gold(dataset: Dataset, work_id: str, gold_key: str) -> str:
    claim = next(
        c for c in dataset.claims if c.research_work_id == work_id and c.gold_key == gold_key
    )
    return stored_claim_id(claim)


def _ranking(dataset: Dataset) -> list[str]:
    return [_gold(dataset, B1, "c1"), _gold(dataset, C1, "c1"), ABSENT]


def _run(store: Store, dataset: Dataset, search: FixedSearch) -> EvaluationReport:
    return evaluate_store(
        store,
        dataset,
        model_identifier="extractor-model-a",
        prompt_version="claims-v1",
        schema_version="core-1",
        now=NOW,
        search=search,
    )


def test_stored_claims_that_equal_the_gold_score_one(store: Store, dataset: Dataset) -> None:
    report = _run(store, dataset, FixedSearch(_ranking(dataset)))

    extraction = report.extraction
    assert extraction is not None
    assert extraction.fields.micro.f1 == 1.0
    assert extraction.fields.micro.precision == 1.0
    assert extraction.fields.micro.recall == 1.0
    assert extraction.field_errors == ()
    assert extraction.unmatched_gold == ()
    assert extraction.unmatched_predicted == ()
    assert extraction.relationships.rate == 1.0
    assert extraction.spans.exact_rate == 1.0
    assert report.created_at == NOW
    assert report.split == "dev"
    assert report.notes == ()


def test_the_study_map_comes_from_the_spans(store: Store, dataset: Dataset) -> None:
    """Every gold study key reaches its stored study, which no ID convention names."""
    report = _run(store, dataset, FixedSearch(_ranking(dataset)))

    extraction = report.extraction
    assert extraction is not None
    assert extraction.relationships.errors == ()
    assert extraction.relationships.correct == len(dataset.claims)
    stored = {study_id(claim.study_key) for claim in dataset.claims}
    assert {c.study_id for c in store.list_claims()} == stored


def test_one_altered_claim_drops_the_extraction_score(dataset: Dataset) -> None:
    altered = _altered_subject(dataset)
    with Store(":memory:") as store:
        seed(store, altered)
        report = _run(store, dataset, FixedSearch(_ranking(dataset)))

    extraction = report.extraction
    assert extraction is not None
    assert extraction.fields.micro.f1 is not None
    assert extraction.fields.micro.f1 < 1.0
    assert extraction.fields.per_field["subject"].recall is not None
    assert extraction.fields.per_field["subject"].recall < 1.0
    assert [(e.gold_key, e.field) for e in extraction.field_errors] == [(f"{B1}:c1", "subject")]
    assert extraction.unmatched_gold == ()


def test_the_search_runs_once_per_gold_query_and_scores_the_ranking(
    store: Store, dataset: Dataset
) -> None:
    search = FixedSearch(_ranking(dataset))

    report = _run(store, dataset, search)

    assert search.queries == [q.query_text for q in dataset.retrievals]
    retrieval = report.retrieval
    assert retrieval is not None
    assert [(q.query_id, q.recall_at_5) for q in retrieval.per_query] == [
        ("q1", 1 / 3),
        ("q2", 1.0),
        ("q3", 0.0),
    ]
    assert [q.returned for q in retrieval.per_query] == [3, 3, 3]


def test_the_search_results_become_stance_predictions(store: Store, dataset: Dataset) -> None:
    report = _run(store, dataset, FixedSearch(_ranking(dataset)))

    stance = report.stance
    assert stance is not None
    # Three gold pairs meet a prediction: q1 with bio1 c1, q2 and q3 with cs1 c1.
    assert stance.labeled == len(dataset.stances)
    assert stance.missing == len(dataset.stances) - 3
    # Six predictions have no gold pair: three on the absent claim, three on other pairs.
    assert stance.extra == 6
    assert stance.confusion["SUPPORTS"]["SUPPORTS"] == 2
    assert stance.confusion["MIXED"]["SUPPORTS"] == 1
    assert stance.comparability_accuracy == 1 / 3


def test_notes_appear_only_when_the_caller_passes_them(store: Store, dataset: Dataset) -> None:
    report = evaluate_store(
        store,
        dataset,
        model_identifier="extractor-model-a",
        prompt_version="claims-v1",
        schema_version="core-1",
        now=NOW,
        search=FixedSearch(()),
        notes=("The papers, the gold labels and the claims are invented test fixtures.",),
    )

    assert report.notes[0].endswith("invented test fixtures.")
    assert "- Note: " in report.to_markdown()


def _altered_subject(dataset: Dataset) -> Dataset:
    """The dataset with the subject of the first claim of the first document changed."""
    document = dataset.documents[0]
    first = document.claims[0].model_copy(
        update={"subject": Term(original="an invented other subject")}
    )
    documents = (
        document.model_copy(update={"claims": (first, *document.claims[1:])}),
        *dataset.documents[1:],
    )
    return dataset.model_copy(update={"documents": documents})
