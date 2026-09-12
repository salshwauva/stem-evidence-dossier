"""Normalization: canonical names and units (plan section 33).

This package imports model and profiles, and never a sibling. The functions
are pure. extract calls normalize_claim through its Normalizer protocol.
"""

from evidence_dossier.normalize.normalize import (
    canonical_name,
    canonical_unit,
    fold_key,
    fold_name,
    normalize_claim,
)
from evidence_dossier.normalize.tables import NAME_SYNONYMS, UNIT_SYNONYMS

__all__ = [
    "NAME_SYNONYMS",
    "UNIT_SYNONYMS",
    "canonical_name",
    "canonical_unit",
    "fold_key",
    "fold_name",
    "normalize_claim",
]
