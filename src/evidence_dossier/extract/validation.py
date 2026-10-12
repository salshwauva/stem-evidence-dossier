"""Schema and relationship validation for extractor output (plan sections 31, 32 and 47).

Validation parses the raw reply and checks its studies and its top-level keys
against CandidateClaims. A reply that fails to parse, has an unknown top-level
key, fails the study schema or repeats a study key fails as a whole. Each claim
then validates alone against CandidateClaim and against the relationships:
its study_key resolves, its evidence section belongs to the document, and its
source_text occurs exactly once in its section. A claim that fails is rejected
alone, and the claims that pass stay. The pipeline computes the offsets from
the section text and never trusts offsets from the model. Every failure is an
error string, so a flawed reply stays stored with its errors.
"""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from evidence_dossier.extract.candidates import CandidateClaim, CandidateClaims, CandidateStudy
from evidence_dossier.model import EvidenceSpan, Section, SourceDocument

# A Markdown code fence with any language tag, or none.
_FENCE = re.compile(r"```[^\n`]*\n(.*?)\n[ \t]*```", re.DOTALL)
_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class AcceptedClaim:
    """A claim that passed validation, with its span and its position in the reply."""

    number: int  # counted from 1, so claim number n has the error prefix "claims.<n - 1>"
    candidate: CandidateClaim
    span: EvidenceSpan


@dataclass(frozen=True)
class ValidationOutcome:
    """The studies and the accepted claims of one reply, and every error.

    studies is None when the reply fails as a whole. Otherwise accepted holds
    the claims that passed, in reply order, and each claim that did not pass
    has an error.
    """

    studies: tuple[CandidateStudy, ...] | None
    accepted: tuple[AcceptedClaim, ...]
    errors: tuple[str, ...]


def slug(key: str) -> str:
    """Return the study key as a lowercase identifier for a study ID."""
    return _SLUG.sub("_", key.casefold()).strip("_")


def validate_response(
    text: str, document: SourceDocument, sections: Sequence[Section]
) -> ValidationOutcome:
    """Validate one raw reply against the schema and against the sections of the document."""
    try:
        envelope, raw_claims = _split_reply(text)
    except ValueError as error:
        return ValidationOutcome(None, (), _error_strings(error))
    errors = _study_errors(envelope.studies)
    if errors:
        return ValidationOutcome(None, (), tuple(errors))
    study_keys = {study.key for study in envelope.studies}
    by_id = {section.id: section for section in sections if section.document_id == document.id}
    accepted: list[AcceptedClaim] = []
    for n, raw in enumerate(raw_claims):
        try:
            claim = CandidateClaim.model_validate(raw)
        except ValidationError as error:
            errors.extend(_error_strings(error, prefix=f"claims.{n}"))
            continue
        span, claim_errors = _check_claim(n, claim, study_keys, by_id, document)
        errors.extend(claim_errors)
        if span is not None:
            accepted.append(AcceptedClaim(number=n + 1, candidate=claim, span=span))
    return ValidationOutcome(envelope.studies, tuple(accepted), tuple(errors))


def _split_reply(text: str) -> tuple[CandidateClaims, list[Any]]:
    """Return the reply without its claims, and its raw claims, which validate one by one.

    A ValueError means the reply fails as a whole.
    """
    data = _parse_json(text)
    if isinstance(data, dict) and isinstance(data.get("claims"), list):
        return CandidateClaims.model_validate({**data, "claims": []}), data["claims"]
    envelope = CandidateClaims.model_validate(data)
    return envelope, list(envelope.claims)


def _check_claim(
    n: int,
    claim: CandidateClaim,
    study_keys: set[str],
    by_id: dict[str, Section],
    document: SourceDocument,
) -> tuple[EvidenceSpan | None, list[str]]:
    """Return the span of claim n, or None and every reason the claim is rejected."""
    errors: list[str] = []
    if claim.study_key not in study_keys:
        errors.append(f"claims.{n}.study_key: {claim.study_key} is not a study of this output")
    section = by_id.get(claim.evidence.section_id)
    if section is None:
        errors.append(
            f"claims.{n}.evidence.section_id: {claim.evidence.section_id}"
            f" is not a section of document {document.id}"
        )
        return None, errors
    source_text = claim.evidence.source_text
    count = section.text.count(source_text)
    if count != 1:
        reason = "does not occur" if count == 0 else f"occurs {count} times"
        errors.append(
            f"claims.{n}.evidence.source_text: {reason} in section {section.id},"
            " so the span is ambiguous or missing"
        )
    if errors:
        return None, errors
    start = section.text.index(source_text)
    span = EvidenceSpan(
        research_work_id=document.research_work_id,
        section_id=section.id,
        start_offset=start,
        end_offset=start + len(source_text),
        source_text=source_text,
    )
    return span, errors


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


def _error_strings(error: ValueError, prefix: str = "") -> tuple[str, ...]:
    if isinstance(error, ValidationError):
        return tuple(
            ".".join(part for part in (prefix, *(str(loc) for loc in item["loc"])) if part)
            + f": {item['msg']}"
            for item in error.errors()
        )
    return (f"response is not JSON: {error}",)


def _study_errors(studies: tuple[CandidateStudy, ...]) -> list[str]:
    errors: list[str] = []
    keys: dict[str, str] = {}
    for n, study in enumerate(studies):
        if study.key in keys:
            errors.append(f"studies.{n}.key: {study.key} appears more than once")
        elif slug(study.key) in keys.values():
            errors.append(f"studies.{n}.key: {study.key} gives the same ID as an earlier key")
        keys[study.key] = slug(study.key)
    return errors
