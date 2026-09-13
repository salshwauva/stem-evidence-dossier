"""Rule based query parser: text to QueryProposition (plan section 34, ADR 0006, ADR 0012).

The parser calls no model. It lowercases the text, finds the first relationship
verb from a fixed table, and splits the subject, the measurement and the
comparator around that verb and a comparator marker. Every rule that fires
lands in parse_notes, so the API can show how the fields came about.

QueryParser is the protocol that a caller needs. DeterministicQueryParser wraps
these rules and stays the default everywhere. The optional model backed parser
lives in query.model_parser and falls back to this one (ADR 0012).
"""

import re
import uuid
from dataclasses import dataclass
from typing import Protocol

from evidence_dossier.model import Domain, QueryProposition, ResultDirection

RULES_NOTE = "parser: the deterministic rules produced this parse"

# An auxiliary and "not" in front of a verb. A negated verb keeps its label and
# loses the expected direction, because "not decreased" names more than one
# direction (ADR 0012).
_NEGATION = r"(?P<negation>(?:does|do|did|is|are|was|were)\s+not\s+|doesn't\s+|don't\s+|didn't\s+)?"


@dataclass(frozen=True)
class _Relationship:
    """One row of the verb table."""

    pattern: re.Pattern[str]
    label: str
    negated_label: str
    direction: ResultDirection
    # True for outperform and underperform: the comparator follows the verb and
    # the measurement follows a context marker after it.
    comparator_first: bool = False


def _verb(
    verbs: str,
    label: str,
    negated_label: str,
    direction: ResultDirection,
    *,
    comparator_first: bool = False,
) -> _Relationship:
    """A row whose verb takes a negation in front of it."""
    return _Relationship(
        re.compile(rf"\b{_NEGATION}(?:{verbs})\b"),
        label,
        negated_label,
        direction,
        comparator_first,
    )


def _fixed(pattern: str, label: str, direction: ResultDirection) -> _Relationship:
    """A row that spells out its own words, such as "has no effect on"."""
    return _Relationship(re.compile(rf"\b(?:{pattern})\b"), label, label, direction)


# The verb table. The parser takes the match that starts first in the text, so
# the order here only breaks a tie between two rows at the same position.
_TABLE: tuple[_Relationship, ...] = (
    _fixed(
        r"(?:does|do|did)\s+not\s+(?:change|affect|alter)", "no change", ResultDirection.UNCHANGED
    ),
    _fixed(r"(?:has|have|had)\s+no\s+effect\s+on", "no change", ResultDirection.UNCHANGED),
    _fixed(
        r"(?:shows?|showed|reports?|reported)\s+no\s+change\s+in",
        "no change",
        ResultDirection.UNCHANGED,
    ),
    _fixed(r"no\s+(?:effect\s+on|change\s+in)", "no change", ResultDirection.UNCHANGED),
    _verb(
        r"increase[sd]?|raise[sd]?|boost(?:s|ed)?",
        "increases",
        "does not increase",
        ResultDirection.INCREASED,
    ),
    _verb(
        r"reduce[sd]?|decrease[sd]?|lower(?:s|ed)?|cuts?",
        "reduces",
        "does not reduce",
        ResultDirection.DECREASED,
    ),
    _verb(r"improve[sd]?|enhance[sd]?", "improves", "does not improve", ResultDirection.IMPROVED),
    _verb(
        r"worsen(?:s|ed)?|degrade[sd]?|harm(?:s|ed)?",
        "worsens",
        "does not worsen",
        ResultDirection.WORSENED,
    ),
    _verb(
        r"outperform(?:s|ed)?",
        "outperforms",
        "does not outperform",
        ResultDirection.IMPROVED,
        comparator_first=True,
    ),
    _verb(
        r"underperform(?:s|ed)?",
        "underperforms",
        "does not underperform",
        ResultDirection.WORSENED,
        comparator_first=True,
    ),
)

_COMPARATOR_MARKER = re.compile(
    r"\bcompared\s+(?:with|to|against)\b|\brelative\s+to\b|\bversus\b|\bvs\b\.?"
    r"|\bagainst\b|\bthan\b|\bover\b"
)
# Leading question words and trailing punctuation that carry no proposition content.
_QUESTION_PREFIX = re.compile(r"^(?:whether|does|do|is|are|can)\s+")
_TRAILING = re.compile(r"[\s?.!]+$")
_ARTICLE = re.compile(r"^(?:the|a|an)\s+")
# Words that sit between the subject and the verb and name no subject.
_SUBJECT_TAIL = re.compile(
    r"\s+(?:significantly|substantially|consistently|slightly|markedly|greatly|is|are|was|were)$"
)
# Where the setting starts, so the measurement phrase ends. "of" stays inside
# the phrase, because "risk of infection" is one measurement.
_CONTEXT_MARKER = re.compile(
    r"\s+(?:by|in|on|at|for|from|across|among|within|during|under|when|while|after)\s+"
)
# A comparison word that belongs to the comparator, not to the measurement.
_COMPARISON_TAIL = re.compile(
    r"\s+(?:more|less|further|better|worse|faster|slower|lower|higher|greater|fewer)$"
)


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
    the text after the verb up to the comparator marker, without the setting
    that follows it, and the comparator is the text after the marker. The
    outperform verbs turn that around: they name the comparator first. When no
    verb matches, the whole text becomes the subject and the relationship is
    "unknown".
    """
    notes: list[str] = []
    cleaned = _TRAILING.sub("", text.strip().lower())
    stripped = _QUESTION_PREFIX.sub("", cleaned)
    if stripped != cleaned:
        notes.append("question: dropped the leading question word")
    found = _find(stripped)
    if found is None:
        notes.append(
            "relationship: no verb from the table matched, so the whole text is the subject"
        )
        notes.append("comparator: no comparator marker found")
        return _proposition(
            text,
            notes,
            subject=_subject_of(stripped, notes),
            relationship="unknown",
            measurement=None,
            comparator=None,
            direction=None,
            domain=domain,
            dataset=dataset,
            system=system,
            population=population,
        )
    row, match = found
    negated = match.groupdict().get("negation") is not None
    label = row.negated_label if negated else row.label
    direction = None if negated else row.direction
    if negated:
        notes.append(f"relationship: matched '{match.group(0)}' as {label}")
        notes.append(
            f"negation: '{match.group('negation').strip()}' negates the verb,"
            " so the parse states no expected direction"
        )
    else:
        notes.append(f"relationship: matched '{match.group(0)}' as {label}, expected {direction}")
    subject = _subject_of(stripped[: match.start()].strip(), notes)
    remainder = stripped[match.end() :].strip()
    if row.comparator_first:
        measurement, comparator = _comparator_first(remainder, notes)
    else:
        measurement, comparator = _measurement_first(remainder, notes)
    return _proposition(
        text,
        notes,
        subject=subject,
        relationship=label,
        measurement=measurement,
        comparator=comparator,
        direction=direction,
        domain=domain,
        dataset=dataset,
        system=system,
        population=population,
    )


def _find(text: str) -> tuple[_Relationship, re.Match[str]] | None:
    """Return the table row whose match starts first in the text."""
    best: tuple[_Relationship, re.Match[str]] | None = None
    for row in _TABLE:
        match = row.pattern.search(text)
        if match is None:
            continue
        if best is None or match.start() < best[1].start():
            best = (row, match)
    return best


def _measurement_first(remainder: str, notes: list[str]) -> tuple[str | None, str | None]:
    """Split the text after the verb into the measurement and the comparator."""
    marker = _COMPARATOR_MARKER.search(remainder)
    if marker is None:
        notes.append("comparator: no comparator marker found")
        return _measurement_of(remainder, notes), None
    notes.append(f"comparator: split on '{marker.group(0)}'")
    return _measurement_of(remainder[: marker.start()], notes), remainder[marker.end() :].strip()


def _comparator_first(remainder: str, notes: list[str]) -> tuple[str | None, str | None]:
    """Split the text after an outperform verb: the comparator comes before the measurement."""
    marker = _CONTEXT_MARKER.search(remainder)
    if marker is None:
        notes.append("comparator: the verb names the comparator, and no measurement follows it")
        return None, remainder.strip() or None
    notes.append(f"comparator: the verb names the comparator, split on '{marker.group(0).strip()}'")
    return _measurement_of(remainder[marker.end() :], notes), remainder[: marker.start()].strip()


def _measurement_of(text: str, notes: list[str]) -> str | None:
    """Return the measurement phrase without its article, its setting or a comparison word."""
    phrase, articles = _ARTICLE.subn("", text.strip(), count=1)
    if articles:
        notes.append("measurement: dropped the leading article")
    marker = _CONTEXT_MARKER.search(phrase)
    if marker is not None:
        notes.append(f"measurement: cut the context that starts at '{marker.group(0).strip()}'")
        phrase = phrase[: marker.start()]
    trimmed = _trim_tail(phrase.strip(), _COMPARISON_TAIL)
    if trimmed != phrase.strip():
        notes.append("measurement: dropped the trailing comparison word")
    return trimmed or None


def _subject_of(text: str, notes: list[str]) -> str:
    """Return the subject without its article and without the adverb before the verb."""
    subject, articles = _ARTICLE.subn("", text.strip(), count=1)
    if articles:
        notes.append("subject: dropped the leading article")
    trimmed = _trim_tail(subject, _SUBJECT_TAIL)
    if trimmed != subject:
        notes.append("subject: dropped the trailing adverb")
    return trimmed


def _trim_tail(text: str, pattern: re.Pattern[str]) -> str:
    """Drop every trailing word that the pattern names."""
    while True:
        trimmed = pattern.sub("", text)
        if trimmed == text:
            return text
        text = trimmed


def _proposition(
    text: str,
    notes: list[str],
    *,
    subject: str,
    relationship: str,
    measurement: str | None,
    comparator: str | None,
    direction: ResultDirection | None,
    domain: Domain | None,
    dataset: str | None,
    system: str | None,
    population: str | None,
) -> QueryProposition:
    """Build the record and close the notes with the domain rule and the parser path."""
    if domain is None:
        notes.append("domain: none given, so retrieval searches every domain")
    notes.append(RULES_NOTE)
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


class QueryParser(Protocol):
    """Anything that turns query text into a typed proposition (plan section 47)."""

    def parse(
        self,
        text: str,
        *,
        domain: Domain | None = None,
        dataset: str | None = None,
        system: str | None = None,
        population: str | None = None,
    ) -> QueryProposition: ...


class DeterministicQueryParser:
    """The rules in this module behind the QueryParser protocol.

    This parser is the default everywhere. It runs no model, so a parse costs
    nothing, repeats exactly, and needs no key.
    """

    def parse(
        self,
        text: str,
        *,
        domain: Domain | None = None,
        dataset: str | None = None,
        system: str | None = None,
        population: str | None = None,
    ) -> QueryProposition:
        return parse_query(
            text, domain=domain, dataset=dataset, system=system, population=population
        )
