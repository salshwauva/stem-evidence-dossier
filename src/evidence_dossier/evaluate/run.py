"""One evaluation run over a store: extraction, retrieval and stance (plan sections 48 and 50).

The caller passes the search as a callable, so this package still imports no
sibling package (ADR 0008). A stored claim reaches its gold key through the
evidence span match of matching.py, never through an ID convention, so the
extractor is free to name its claims and its studies as it likes.
"""

from collections.abc import Callable, Sequence
from datetime import datetime

from evidence_dossier.evaluate.extraction import run_extraction_evaluation
from evidence_dossier.evaluate.gold import Dataset
from evidence_dossier.evaluate.matching import match_claims
from evidence_dossier.evaluate.report import EvaluationReport
from evidence_dossier.evaluate.retrieval import run_retrieval_evaluation
from evidence_dossier.evaluate.stance import StancePrediction, run_stance_evaluation
from evidence_dossier.model import ComparabilityLevel, EvidenceClaim, FrozenModel, Stance
from evidence_dossier.store import Store


class SearchHit(FrozenModel):
    """One search result in rank order, reduced to the values that scoring needs."""

    claim_id: str
    stance: Stance
    comparability: ComparabilityLevel
    reason: str = ""


type SearchCallable = Callable[[Store, str], Sequence[SearchHit]]


def stored_claims(store: Store, dataset: Dataset) -> list[EvidenceClaim]:
    """Return the stored claims of every research work in the dataset, in claim ID order."""
    claims: list[EvidenceClaim] = []
    for document in dataset.documents:
        claims.extend(store.list_claims(research_work_id=document.research_work_id))
    return claims


def gold_keys(
    dataset: Dataset, predicted: Sequence[EvidenceClaim]
) -> tuple[dict[str, str], dict[str, str]]:
    """Return the claim ID to gold key map and the gold study key to study ID map.

    Both maps come from the span match: a matched pair says that this stored
    claim is that gold claim, so its study is the study of that gold key. Two
    gold claims of one study key that match claims of different studies keep
    the first pair in match order, and the relationship score then counts the
    others as errors.
    """
    matching = match_claims(dataset.claims, tuple(predicted))
    claim_keys: dict[str, str] = {}
    study_map: dict[str, str] = {}
    for gold, claim in matching.pairs:
        claim_keys[claim.id] = gold.claim_key
        study_map.setdefault(gold.study_key, claim.study_id)
    return claim_keys, study_map


def evaluate_store(
    store: Store,
    dataset: Dataset,
    *,
    model_identifier: str,
    prompt_version: str,
    schema_version: str,
    now: datetime,
    search: SearchCallable,
    notes: tuple[str, ...] = (),
) -> EvaluationReport:
    """Score the stored claims and the search results of one store against one dataset.

    search runs once per gold query and feeds both the retrieval scores and the
    stance scores. A search result whose claim has no gold claim keeps its
    stored ID, so it holds its rank position and counts as a miss.
    """
    predicted = stored_claims(store, dataset)
    claim_keys, study_map = gold_keys(dataset, predicted)
    ranked: dict[str, list[str]] = {}
    predictions: list[StancePrediction] = []
    for query in dataset.retrievals:
        hits = list(search(store, query.query_text))
        ranked[query.query_id] = [claim_keys.get(hit.claim_id, hit.claim_id) for hit in hits]
        predictions.extend(
            StancePrediction(
                query_id=query.query_id,
                claim_id=claim_keys.get(hit.claim_id, hit.claim_id),
                stance=hit.stance,
                comparability=hit.comparability,
                reason=hit.reason,
            )
            for hit in hits
        )
    return EvaluationReport(
        model_identifier=model_identifier,
        prompt_version=prompt_version,
        schema_version=schema_version,
        split=dataset.split,
        created_at=now,
        extraction=run_extraction_evaluation(dataset, predicted, study_map=study_map),
        retrieval=run_retrieval_evaluation(dataset, ranked),
        stance=run_stance_evaluation(dataset, predictions),
        notes=notes,
    )
