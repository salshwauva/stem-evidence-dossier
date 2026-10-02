"""Schema and relationship validation for extractor output (plan sections 31, 32 and 47).

Validation parses the raw reply, validates it against CandidateClaims, then
checks the relationships: every study_key resolves, every evidence section
belongs to the document, and every source_text occurs exactly once in its
section. The pipeline computes the offsets from the section text and never
trusts offsets from the model. Every failure is an error string, so an
invalid reply stays stored with its errors.

The section text keeps Unicode spaces such as the no-break space, and a model
reply often copies one of them as a plain space. A source_text that does not
occur exactly is retried with each plain space matching any such space. The
match is one character for one character, so the stored span holds the exact
section text and its offsets stay inside the section.
"""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from evidence_dossier.extract.candidates import CandidateClaims
from evidence_dossier.model import EvidenceSpan, Section, SourceDocument

# A Markdown code fence with any language tag, or none.
_FENCE = re.compile(r"```[^\n`]*\n(.*?)\n[ \t]*```", re.DOTALL)
_SLUG = re.compile(r"[^a-z0-9]+")
# Characters that a reply may copy as a plain space: tab and the Unicode space separators.
_SPACE_LIKE = "[ \t\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]"


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
        found = _occurrences(section.text, claim.evidence.source_text)
        if len(found) != 1:
            reason = "does not occur" if not found else f"occurs {len(found)} times"
            errors.append(
                f"claims.{n}.evidence.source_text: {reason} in section {section.id},"
                " so the span is ambiguous or missing"
            )
            continue
        start, end = found[0]
        spans.append(
            EvidenceSpan(
                research_work_id=document.research_work_id,
                section_id=section.id,
                start_offset=start,
                end_offset=end,
                source_text=section.text[start:end],
            )
        )
    if errors:
        return ValidationOutcome(None, (), tuple(errors))
    return ValidationOutcome(candidates, tuple(spans), ())


def _occurrences(section_text: str, source_text: str) -> list[tuple[int, int]]:
    """Return the start and end of each place where the source text occurs in the section.

    An exact match wins. Without one, each plain space of the source text matches
    any space-like character, one for one.
    """
    exact = [m.span() for m in re.finditer(re.escape(source_text), section_text)]
    if exact:
        return exact
    pattern = _SPACE_LIKE.join(re.escape(word) for word in source_text.split(" "))
    return [m.span() for m in re.finditer(pattern, section_text)]


def _parse_json(text: str) -> Any:
    """Return the JSON of a reply: its one fenced JSON block, or else the whole reply.

    A fenced block that is not JSON, such as quoted text, drops out. Two fenced
    JSON blocks make the reply ambiguous. Prose around unfenced JSON fails the
    parse, so the run is stored INVALID with its raw reply.
    """
    fenced = _json_blocks(_FENCE.findall(text))
    if len(fenced) > 1:
        raise ValueError(f"the reply holds {len(fenced)} fenced JSON blocks, so it is ambiguous")
    return fenced[0] if fenced else json.loads(text)


def _json_blocks(blocks: list[str]) -> list[Any]:
    values: list[Any] = []
    for block in blocks:
        try:
            values.append(json.loads(block))
        except json.JSONDecodeError:
            continue
    return values


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
