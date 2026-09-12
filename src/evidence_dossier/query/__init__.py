"""Query parsing, retrieval, comparability and stance (plan sections 34 to 39).

This package imports model, profiles and store. It imports no sibling
subpackage. Canonical names reach it through an injected canonicalizer.
"""

from evidence_dossier.query.models import (
    EXPECTED_DIRECTIONS,
    ComparabilityAssessment,
    DimensionComparison,
    EvidenceFilters,
    EvidenceHit,
    EvidenceSearchResult,
    QueryProposition,
    Relationship,
    StanceAssessment,
)
from evidence_dossier.query.parser import (
    COMPARATOR_MARKERS,
    PARSER_VERSION,
    RELATION_WORDS,
    DeterministicQueryParser,
    FallbackParser,
    QueryParseError,
    QueryParser,
)
from evidence_dossier.query.text import Canonicalizer, default_canonicalizer

__all__ = [
    "COMPARATOR_MARKERS",
    "EXPECTED_DIRECTIONS",
    "PARSER_VERSION",
    "RELATION_WORDS",
    "Canonicalizer",
    "ComparabilityAssessment",
    "DeterministicQueryParser",
    "DimensionComparison",
    "EvidenceFilters",
    "EvidenceHit",
    "EvidenceSearchResult",
    "FallbackParser",
    "QueryParseError",
    "QueryParser",
    "QueryProposition",
    "Relationship",
    "StanceAssessment",
    "default_canonicalizer",
]
