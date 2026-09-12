"""Query parser, retrieval, comparability and stance (plan sections 34 to 39).

This package imports model, profiles and store, and nothing else from
evidence_dossier.
"""

from evidence_dossier.model import Dossier, QueryProposition, StanceAssessment
from evidence_dossier.query.comparability import (
    MATCH_THRESHOLD,
    ComparabilityAssessment,
    ComparabilityEngine,
    DimensionResult,
)
from evidence_dossier.query.parser import parse_query
from evidence_dossier.query.polarity import POLARITY_VERSION, Polarity, polarity_of
from evidence_dossier.query.retrieval import Candidate, Retriever
from evidence_dossier.query.search import (
    STANCE_ORDER,
    EvidenceItem,
    EvidenceResults,
    Provenance,
    StanceGroup,
    build_dossier,
    search_evidence,
)
from evidence_dossier.query.stance import StanceClassifier

__all__ = [
    "MATCH_THRESHOLD",
    "POLARITY_VERSION",
    "STANCE_ORDER",
    "Candidate",
    "ComparabilityAssessment",
    "ComparabilityEngine",
    "DimensionResult",
    "Dossier",
    "EvidenceItem",
    "EvidenceResults",
    "Polarity",
    "Provenance",
    "QueryProposition",
    "Retriever",
    "StanceAssessment",
    "StanceClassifier",
    "StanceGroup",
    "build_dossier",
    "parse_query",
    "polarity_of",
    "search_evidence",
]
