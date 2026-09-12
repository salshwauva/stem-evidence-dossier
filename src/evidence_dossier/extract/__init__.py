"""Extraction: prompt, provider adapter, boundary models, validation and the pipeline.

This package imports model, profiles and store, and never a sibling. The
pipeline takes a normalizer as an argument (the Normalizer protocol in
pipeline.py), so extract never imports normalize (plan sections 31, 47 and 51).
"""

from evidence_dossier.extract.candidates import (
    CandidateClaim,
    CandidateClaims,
    CandidateEvidence,
    CandidateStudy,
)
from evidence_dossier.extract.pipeline import Normalizer, extract_document
from evidence_dossier.extract.prompt import PROMPT_VERSION, build_prompt
from evidence_dossier.extract.providers import (
    ClaudeCliProvider,
    ExtractionProvider,
    ProviderError,
    ProviderResponse,
    RecordedProvider,
    prompt_key,
)
from evidence_dossier.extract.validation import ValidationOutcome, validate_response

__all__ = [
    "PROMPT_VERSION",
    "CandidateClaim",
    "CandidateClaims",
    "CandidateEvidence",
    "CandidateStudy",
    "ClaudeCliProvider",
    "ExtractionProvider",
    "Normalizer",
    "ProviderError",
    "ProviderResponse",
    "RecordedProvider",
    "ValidationOutcome",
    "build_prompt",
    "extract_document",
    "prompt_key",
    "validate_response",
]
