"""Measurement polarity: does a lower number or a higher number mean a better result?

Plan section 21 keeps the directions INCREASED and DECREASED apart from IMPROVED
and WORSENED. A magnitude direction and a quality direction only line up when the
reader knows which way the measurement points. This module holds that knowledge as
a versioned table, so the stance classifier states its assumption instead of
guessing one (plan section 39).

The table is keyed on the folded measurement name. fold reuses the token rules of
query.text, so a key matches a claim measurement whatever its case, its spacing or
its hyphens.
"""

from enum import StrEnum

from evidence_dossier.query.text import tokens

# Version of the table below. The stance reason names it, so a stored assessment
# says which table decided the stance. A new or changed entry needs a new version.
POLARITY_VERSION = "polarity-v3"


class Polarity(StrEnum):
    """Which way a measurement points when the result gets better."""

    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"


def fold(name: str) -> str:
    """Return the table key for a measurement name.

    The fold lowercases the name, drops the query stopwords, and joins the word
    tokens with one space. Hyphens and runs of whitespace fall out with the
    tokens, so "Factual-Error  Rate" and "factual error rate" fold alike.
    """
    return " ".join(tokens(name))


# Seed entries, from the measurements that the plan examples and the test corpus name.
# Each key is written folded, because the lookup folds the name it receives.
# A measurement whose better direction depends on the context stays out. Temperature,
# pressure and wavelength are measurements of that kind, so the physics profile adds
# no entry here and the stance classifier reports the missing polarity instead.
_SEED: dict[Polarity, tuple[str, ...]] = {
    Polarity.LOWER_IS_BETTER: (
        "error rate",
        "factual error rate",
        "hallucination rate",
        "latency",
        "loss",
        "perplexity",
        "energy consumption",
        "memory use",
        "defect rate",
        "cycle time",
    ),
    Polarity.HIGHER_IS_BETTER: (
        "accuracy",
        "f1",
        "precision",
        "recall",
        "throughput",
        "yield",
        "selectivity",
        "cell viability",
        "neuronal survival",
        "protein abundance",
        "tensile strength",
        "yield strength",
        "efficiency",
    ),
}

TABLE: dict[str, Polarity] = {
    fold(name): polarity for polarity, names in _SEED.items() for name in names
}


def polarity_of(name: str | None) -> Polarity | None:
    """Return the polarity of a measurement name, or None when the table does not know it.

    The lookup uses the exact folded key. A name that the table does not hold gives
    None, and the caller reports that the polarity is missing rather than assuming one.
    A trailing "rate" says nothing about the direction ("success rate" and "error rate"
    point opposite ways), so v3 dropped the suffix rule that v2 had.
    """
    if name is None:
        return None
    key = fold(name)
    if not key:
        return None
    return TABLE.get(key)
