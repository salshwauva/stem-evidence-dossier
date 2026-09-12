"""Rule based query parser: text to QueryProposition (plan section 34, ADR 0006).

The parser calls no model. It lowercases the text, finds one relationship verb
from a fixed table, and splits the subject, the measurement and the comparator
around that verb and a comparator marker. Every rule that fires lands in
parse_notes, so the API can show how the fields came about.
"""

import re
import uuid

from evidence_dossier.model import Domain, QueryProposition, ResultDirection

# Relationship patterns in the order the parser tries them. A negated form comes
# before the plain verb it contains.
_RELATIONSHIPS: tuple[tuple[str, str, ResultDirection], ...] = (
    (r"does not (?:change|affect|alter)", "does not change", ResultDirection.UNCHANGED),
    (r"has no effect on", "no effect", ResultDirection.UNCHANGED),
    (
        r"reduces?|reduced|decreases?|decreased|lowers?|lowered",
        "reduces",
        ResultDirection.DECREASED,
    ),
    (r"increases?|increased|raises?|raised", "increases", ResultDirection.INCREASED),
    (r"improves?|improved", "improves", ResultDirection.IMPROVED),
    (r"worsens?|worsened", "worsens", ResultDirection.WORSENED),
)
_RELATIONSHIP_PATTERNS = tuple(
    (re.compile(rf"\b(?:{pattern})\b"), label, direction)
    for pattern, label, direction in _RELATIONSHIPS
)
_COMPARATOR_MARKER = re.compile(r"\b(?:compared (?:with|to)|versus|vs\.?|relative to|than)\b")
# Leading question words and trailing punctuation that carry no proposition content.
_QUESTION_PREFIX = re.compile(r"^(?:whether|does|do|is|are|can)\s+")
_TRAILING = re.compile(r"[\s?.!]+$")


def parse_query(
    text: str,
    *,
    domain: Domain | None = None,
    dataset: str | None = None,
    system: str | None = None,
    population: str | None = None,
) -> QueryProposition:
    """Parse a question or a statement into a QueryProposition with the same rules every time.

    The subject is the text before the relationship verb. The measurement is
    the text after the verb up to the comparator marker, and the comparator is
    the text after the marker. When no verb matches, the whole text becomes the
    subject and the relationship is "unknown".
    """
    notes: list[str] = []
    cleaned = _TRAILING.sub("", text.strip().lower())
    stripped = _QUESTION_PREFIX.sub("", cleaned)
    if stripped != cleaned:
        notes.append("question: dropped the leading question word")
    relationship = "unknown"
    direction: ResultDirection | None = None
    subject = stripped
    remainder = ""
    for pattern, label, candidate in _RELATIONSHIP_PATTERNS:
        found = pattern.search(stripped)
        if found is None:
            continue
        relationship, direction = label, candidate
        subject = stripped[: found.start()].strip()
        remainder = stripped[found.end() :].strip()
        notes.append(f"relationship: matched '{found.group(0)}' as {label}, expected {candidate}")
        break
    else:
        notes.append(
            "relationship: no verb from the table matched, so the whole text is the subject"
        )
    measurement: str | None = None
    comparator: str | None = None
    marker = _COMPARATOR_MARKER.search(remainder)
    if marker is not None:
        measurement = remainder[: marker.start()].strip() or None
        comparator = remainder[marker.end() :].strip() or None
        notes.append(f"comparator: split on '{marker.group(0)}'")
    else:
        measurement = remainder or None
        notes.append("comparator: no comparator marker found")
    if domain is None:
        notes.append("domain: none given, so retrieval searches every domain")
    return QueryProposition(
        id=f"query_{uuid.uuid4().hex[:16]}",
        text=text,
        domain=domain,
        subject=subject,
        relationship=relationship,
        measurement=measurement,
        comparator=comparator,
        expected_direction=direction,
        dataset=dataset,
        system=system,
        population=population,
        parse_notes=tuple(notes),
    )
