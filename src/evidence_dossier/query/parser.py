"""The deterministic query parser (plan section 34).

The parser reads three documented relations and one documented comparator
marker. It never guesses a field that the text does not state, because an
invented organism, dataset or baseline would change what the query asks.
"""

import re
from collections.abc import Mapping
from typing import Protocol

from evidence_dossier.model import Domain, Term
from evidence_dossier.query.models import EXPECTED_DIRECTIONS, QueryProposition, Relationship
from evidence_dossier.query.text import Canonicalizer, default_canonicalizer

PARSER_VERSION = "deterministic-1"

# The relation words that the parser reads. Plan sections 7 and 34 document them.
RELATION_WORDS: Mapping[str, Relationship] = {
    "increases": Relationship.INCREASES,
    "increase": Relationship.INCREASES,
    "reduces": Relationship.REDUCES,
    "reduce": Relationship.REDUCES,
    "improves": Relationship.IMPROVES,
    "improve": Relationship.IMPROVES,
}

# The comparator marker of plan section 7, in its two spellings.
COMPARATOR_MARKERS: tuple[str, ...] = ("compared with", "compared to")

_RELATION_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(RELATION_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_COMPARATOR_PATTERN = re.compile(
    r"\b(" + "|".join(COMPARATOR_MARKERS) + r")\b",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")
_TRAILING = " .;,"


class QueryParseError(ValueError):
    """The parser did not find a documented proposition in the text."""


class QueryParser(Protocol):
    """The parser interface that the query service depends on."""

    def parse(self, text: str, *, domain: Domain | None = None) -> QueryProposition:
        """Return the typed proposition for one piece of query text."""
        ...


class FallbackParser(Protocol):
    """A parser that runs only after the deterministic rules fail."""

    def __call__(self, text: str, *, domain: Domain | None = None) -> QueryProposition:
        """Return the typed proposition for one piece of query text."""
        ...


class DeterministicQueryParser:
    """A rule parser for the documented proposition forms.

    The grammar is one sentence: a subject, one relation word, a measurement and
    an optional comparator clause. Text without a relation word raises
    QueryParseError, or goes to the fallback parser when a caller injects one.
    """

    def __init__(
        self,
        *,
        canonicalizer: Canonicalizer = default_canonicalizer,
        fallback: FallbackParser | None = None,
    ) -> None:
        self._canonicalize = canonicalizer
        self._fallback = fallback

    def parse(self, text: str, *, domain: Domain | None = None) -> QueryProposition:
        """Return the typed proposition for one piece of query text.

        Raises QueryParseError when the text states no documented relation and
        no fallback parser is available.
        """
        try:
            return self._parse_by_rules(text, domain=domain)
        except QueryParseError:
            if self._fallback is None:
                raise
            return self._fallback(text, domain=domain)

    def _parse_by_rules(self, text: str, *, domain: Domain | None) -> QueryProposition:
        sentence = _WHITESPACE.sub(" ", text).strip().rstrip(_TRAILING)
        head, comparator_text = _split_comparator(sentence)
        match = _RELATION_PATTERN.search(head)
        if match is None:
            raise QueryParseError(
                f"no documented relation in {text!r}. The parser reads {_documented_relations()}."
            )
        subject_text = head[: match.start()].strip(_TRAILING)
        measurement_text = head[match.end() :].strip(_TRAILING)
        if not subject_text:
            raise QueryParseError(f"no subject before {match.group(1)!r} in {text!r}")
        if not measurement_text:
            raise QueryParseError(f"no measurement after {match.group(1)!r} in {text!r}")
        relationship = RELATION_WORDS[match.group(1).lower()]
        return QueryProposition(
            original_text=text,
            domain=domain,
            subject=self._term(subject_text),
            relationship=relationship,
            measurement=self._term(measurement_text),
            comparator=None if comparator_text is None else self._term(comparator_text),
            expected_direction=EXPECTED_DIRECTIONS[relationship],
            parser_version=PARSER_VERSION,
            unresolved_fields=_unresolved(domain, comparator_text),
        )

    def _term(self, text: str) -> Term:
        return Term(original=text, canonical=self._canonicalize(text))


def _split_comparator(sentence: str) -> tuple[str, str | None]:
    """Split a sentence at its comparator marker. The marker itself falls away."""
    match = _COMPARATOR_PATTERN.search(sentence)
    if match is None:
        return sentence, None
    comparator = sentence[match.end() :].strip(_TRAILING)
    return sentence[: match.start()].strip(_TRAILING), comparator or None


def _unresolved(domain: Domain | None, comparator_text: str | None) -> tuple[str, ...]:
    """Name the fields that the text left open. The parser fills none of them."""
    fields = ["method", "context"]
    if domain is None:
        fields.append("domain")
    if comparator_text is None:
        fields.append("comparator")
    return tuple(sorted(fields))


def _documented_relations() -> str:
    names = sorted({word for word in RELATION_WORDS if word.endswith("s")})
    return ", ".join(names)
