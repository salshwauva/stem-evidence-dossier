"""Token helpers that the parser, the retriever and the comparability engine share."""

import re

_TOKEN = re.compile(r"[0-9a-z]+")

# Function words that carry no evidence. They stay out of FTS queries and overlap scores.
STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "by",
        "do",
        "does",
        "for",
        "from",
        "in",
        "is",
        "it",
        "its",
        "no",
        "not",
        "of",
        "on",
        "or",
        "same",
        "than",
        "that",
        "the",
        "this",
        "to",
        "with",
        "without",
    }
)


def tokens(text: str | None) -> tuple[str, ...]:
    """Return the lowercase word tokens of a text, without stopwords and in source order."""
    if text is None:
        return ()
    seen: dict[str, None] = {}
    for token in _TOKEN.findall(text.lower()):
        if token not in STOPWORDS:
            seen.setdefault(token, None)
    return tuple(seen)


def overlap(query_text: str | None, claim_text: str | None) -> float:
    """Return the share of the query tokens that the claim text holds, from 0.0 to 1.0.

    The share counts query tokens, so a long claim text does not dilute a short
    query. An empty query side gives 0.0.
    """
    query_tokens = tokens(query_text)
    if not query_tokens:
        return 0.0
    claim_tokens = set(tokens(claim_text))
    return sum(token in claim_tokens for token in query_tokens) / len(query_tokens)
