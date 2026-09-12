"""Retrieval scoring: Recall@5, Recall@10 and Precision@10 per query (plan section 50).

Recall@k divides the relevant claims in the top k by the relevant claims of
the query, so a query without relevant claims is not assessable. Precision@10
divides by 10, so a short ranking earns less.
"""

from collections.abc import Mapping, Sequence

from evidence_dossier.evaluate.gold import Dataset
from evidence_dossier.evaluate.scores import mean, ratio
from evidence_dossier.model import FrozenModel


class QueryRetrievalScore(FrozenModel):
    query_id: str
    relevant: int
    returned: int
    recall_at_5: float | None
    recall_at_10: float | None
    precision_at_10: float


class RetrievalEvaluation(FrozenModel):
    per_query: tuple[QueryRetrievalScore, ...]
    recall_at_5: float | None
    recall_at_10: float | None
    precision_at_10: float | None


def run_retrieval_evaluation(
    gold: Dataset, ranked: Mapping[str, Sequence[str]]
) -> RetrievalEvaluation:
    """Score the ranked claim IDs of each gold query. A query with no ranking scores as empty."""
    per_query: list[QueryRetrievalScore] = []
    for query in sorted(gold.retrievals, key=lambda q: q.query_id):
        ids = list(dict.fromkeys(ranked.get(query.query_id, ())))
        hits_5 = len(query.relevant_claim_ids.intersection(ids[:5]))
        hits_10 = len(query.relevant_claim_ids.intersection(ids[:10]))
        per_query.append(
            QueryRetrievalScore(
                query_id=query.query_id,
                relevant=len(query.relevant_claim_ids),
                returned=len(ids),
                recall_at_5=ratio(hits_5, len(query.relevant_claim_ids)),
                recall_at_10=ratio(hits_10, len(query.relevant_claim_ids)),
                precision_at_10=hits_10 / 10,
            )
        )
    return RetrievalEvaluation(
        per_query=tuple(per_query),
        recall_at_5=mean(q.recall_at_5 for q in per_query),
        recall_at_10=mean(q.recall_at_10 for q in per_query),
        precision_at_10=mean(q.precision_at_10 for q in per_query),
    )
