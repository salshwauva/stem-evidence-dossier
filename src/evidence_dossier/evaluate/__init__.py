"""Gold labels, dataset splits and scoring (plan sections 49 and 50).

This package imports model, profiles and store only. It scores plain data that
the caller passes in, and it takes the search as a callable (ADR 0008), so it
never imports the extract or query packages.
"""

from evidence_dossier.evaluate.extraction import (
    FIELDS,
    ExtractionEvaluation,
    FieldError,
    FieldScores,
    RelationshipError,
    RelationshipScore,
    SpanMismatch,
    SpanScore,
    run_extraction_evaluation,
    term_value,
)
from evidence_dossier.evaluate.gold import (
    Dataset,
    GoldClaim,
    GoldDocument,
    GoldRetrieval,
    GoldStance,
    Split,
    load_dataset,
)
from evidence_dossier.evaluate.matching import (
    OVERLAP_THRESHOLD,
    Matching,
    match_claims,
    span_jaccard,
    spans_overlap,
)
from evidence_dossier.evaluate.report import NOT_ASSESSABLE, EvaluationReport
from evidence_dossier.evaluate.retrieval import (
    QueryRetrievalScore,
    RetrievalEvaluation,
    run_retrieval_evaluation,
)
from evidence_dossier.evaluate.run import (
    SearchCallable,
    SearchHit,
    evaluate_store,
    gold_keys,
    stored_claims,
)
from evidence_dossier.evaluate.scores import PRF, Counts
from evidence_dossier.evaluate.split import DatasetSplitter
from evidence_dossier.evaluate.stance import (
    ComparabilityMiss,
    StanceEvaluation,
    StancePrediction,
    run_stance_evaluation,
)
from evidence_dossier.evaluate.stop_sheet import (
    COHORT_KEYWORDS,
    Fetch,
    StoppedTrial,
    draw_batch,
    fetch_stopped_trials,
    in_cohort,
    write_key,
    write_sheet,
)

__all__ = [
    "COHORT_KEYWORDS",
    "FIELDS",
    "NOT_ASSESSABLE",
    "OVERLAP_THRESHOLD",
    "PRF",
    "ComparabilityMiss",
    "Counts",
    "Dataset",
    "DatasetSplitter",
    "EvaluationReport",
    "ExtractionEvaluation",
    "Fetch",
    "FieldError",
    "FieldScores",
    "GoldClaim",
    "GoldDocument",
    "GoldRetrieval",
    "GoldStance",
    "Matching",
    "QueryRetrievalScore",
    "RelationshipError",
    "RelationshipScore",
    "RetrievalEvaluation",
    "SearchCallable",
    "SearchHit",
    "SpanMismatch",
    "SpanScore",
    "Split",
    "StanceEvaluation",
    "StancePrediction",
    "StoppedTrial",
    "draw_batch",
    "evaluate_store",
    "fetch_stopped_trials",
    "gold_keys",
    "in_cohort",
    "load_dataset",
    "match_claims",
    "run_extraction_evaluation",
    "run_retrieval_evaluation",
    "run_stance_evaluation",
    "span_jaccard",
    "spans_overlap",
    "stored_claims",
    "term_value",
    "write_key",
    "write_sheet",
]
