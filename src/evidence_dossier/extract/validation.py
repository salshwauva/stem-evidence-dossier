"""Schema and relationship validation for extractor output (plan sections 31, 32 and 47).

Validation parses the raw reply, validates it against CandidateClaims, then
checks the relationships: every study_key resolves, every evidence section
belongs to the document, and every source_text occurs exactly once in its
section. The pipeline computes the offsets from the section text and never
trusts offsets from the model. Every failure is an error string, so an
invalid reply stays stored with its errors.
"""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from evidence_dossier.extract.candidates import CandidateClaims
from evidence_dossier.model import EvidenceSpan, Section, SourceDocument

# A reply wrapped in a Markdown code fence, with or without the json tag.
_FENCE = re.compile(r"\A\s*```(?:json)?\s*\n(.*?)\n\s*```\s*\Z", re.DOTALL)
_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ValidationOutcome:
    """The validated candidates with one span per claim, or the errors."""

    candidates: CandidateClaims | None
    # One span per claim, in claim order. Empty when there are errors.
    spans: tuple[EvidenceSpan, ...]
    errors: tuple[str, ...]


def slug(key: str) -> str:
    """Return the study key as a lowercase identifier for a study ID."""
    return _SLUG.sub("_", key.casefold()).strip("_")


def validate_response(
    text: str, document: SourceDocument, sections: Sequence[Section]
) -> ValidationOutcome:
    """Validate one raw reply against the schema and against the sections of the document."""
    try:
        candidates = CandidateClaims.model_validate(_parse_json(text))
    except ValueError as error:
        return ValidationOutcome(None, (), _error_strings(error))
    errors = _study_errors(candidates)
    spans: list[EvidenceSpan] = []
    by_id = {section.id: section for section in sections if section.document_id == document.id}
    for n, claim in enumerate(candidates.claims):
        section = by_id.get(claim.evidence.section_id)
        if section is None:
            errors.append(
                f"claims.{n}.evidence.section_id: {claim.evidence.section_id}"
                f" is not a section of document {document.id}"
            )
            continue
        count = section.text.count(claim.evidence.source_text)
        if count != 1:
            reason = "does not occur" if count == 0 else f"occurs {count} times"
            errors.append(
                f"claims.{n}.evidence.source_text: {reason} in section {section.id},"
                " so the span is ambiguous or missing"
            )
            continue
        start = section.text.index(claim.evidence.source_text)
        spans.append(
            EvidenceSpan(
                research_work_id=document.research_work_id,
                section_id=section.id,
                start_offset=start,
                end_offset=start + len(claim.evidence.source_text),
                source_text=claim.evidence.source_text,
            )
        )
    if errors:
        return ValidationOutcome(None, (), tuple(errors))
    return ValidationOutcome(candidates, tuple(spans), ())


def _parse_json(text: str) -> Any:
    match = _FENCE.match(text)
    return json.loads(match.group(1) if match else text)


def _error_strings(error: ValueError) -> tuple[str, ...]:
    if isinstance(error, ValidationError):
        return tuple(
            ".".join(str(part) for part in item["loc"]) + f": {item['msg']}"
            for item in error.errors()
        )
    return (f"response is not JSON: {error}",)


def _study_errors(candidates: CandidateClaims) -> list[str]:
    errors: list[str] = []
    keys: dict[str, str] = {}
    for n, study in enumerate(candidates.studies):
        if study.key in keys:
            errors.append(f"studies.{n}.key: {study.key} appears more than once")
        elif slug(study.key) in keys.values():
            errors.append(f"studies.{n}.key: {study.key} gives the same ID as an earlier key")
        keys[study.key] = slug(study.key)
    for n, claim in enumerate(candidates.claims):
        if claim.study_key not in keys:
            errors.append(f"claims.{n}.study_key: {claim.study_key} is not a study of this output")
    return errors
