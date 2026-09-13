import pytest

from evidence_dossier.query.polarity import (
    POLARITY_VERSION,
    TABLE,
    Polarity,
    fold,
    polarity_of,
)
from evidence_dossier.query.text import tokens


def test_the_table_carries_a_version_that_the_stance_reason_can_name() -> None:
    assert POLARITY_VERSION == "polarity-v2"


@pytest.mark.parametrize(
    ("name", "polarity"),
    [
        ("factual error rate", Polarity.LOWER_IS_BETTER),
        ("hallucination rate", Polarity.LOWER_IS_BETTER),
        ("latency", Polarity.LOWER_IS_BETTER),
        ("perplexity", Polarity.LOWER_IS_BETTER),
        ("energy consumption", Polarity.LOWER_IS_BETTER),
        ("memory use", Polarity.LOWER_IS_BETTER),
        ("accuracy", Polarity.HIGHER_IS_BETTER),
        ("F1", Polarity.HIGHER_IS_BETTER),
        ("throughput", Polarity.HIGHER_IS_BETTER),
        ("cell viability", Polarity.HIGHER_IS_BETTER),
        ("neuronal survival", Polarity.HIGHER_IS_BETTER),
        ("tensile strength", Polarity.HIGHER_IS_BETTER),
        ("cycle time", Polarity.LOWER_IS_BETTER),
        ("efficiency", Polarity.HIGHER_IS_BETTER),
        ("yield strength", Polarity.HIGHER_IS_BETTER),
    ],
)
def test_an_exact_key_gives_the_seeded_polarity(name: str, polarity: Polarity) -> None:
    assert polarity_of(name) is polarity


@pytest.mark.parametrize(
    ("written", "polarity"),
    [
        ("Cycle Time", Polarity.LOWER_IS_BETTER),
        ("cycle-time", Polarity.LOWER_IS_BETTER),
        ("the Cycle  Time", Polarity.LOWER_IS_BETTER),
        ("Yield Strength", Polarity.HIGHER_IS_BETTER),
        ("Yield-Strength", Polarity.HIGHER_IS_BETTER),
        ("Efficiency", Polarity.HIGHER_IS_BETTER),
    ],
)
def test_a_raw_measurement_name_reaches_its_folded_entry(written: str, polarity: Polarity) -> None:
    """A table key is folded, and a claim names a measurement however the paper wrote it."""
    assert written not in TABLE
    assert fold(written) in TABLE
    assert polarity_of(written) is polarity


@pytest.mark.parametrize("name", ["temperature", "pressure", "refractive index"])
def test_a_physics_measurement_keeps_no_direction(name: str) -> None:
    """Section 20 measurements whose better direction depends on the context stay out."""
    assert polarity_of(name) is None


@pytest.mark.parametrize("name", ["refusal rate", "annotation error", "Crash-Rate"])
def test_a_name_that_ends_in_rate_or_error_is_lower_is_better(name: str) -> None:
    """The suffix rule answers for names that the seeded table does not list."""
    assert fold(name) not in TABLE
    assert polarity_of(name) is Polarity.LOWER_IS_BETTER


@pytest.mark.parametrize("name", ["error bar chart", "rated throughput"])
def test_the_suffix_rule_reads_the_last_token_only(name: str) -> None:
    assert polarity_of(name) is None


@pytest.mark.parametrize("name", [None, "", "   ", "widget sparkle", "answer quality"])
def test_an_unknown_measurement_has_no_polarity(name: str | None) -> None:
    assert polarity_of(name) is None


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        ("Factual-Error  Rate", "factual error rate"),
        ("FACTUAL ERROR RATE", "factual error rate"),
        ("the factual error rate", "factual error rate"),
        ("cell-viability", "cell viability"),
    ],
)
def test_a_name_folds_the_same_way_as_query_text(written: str, expected: str) -> None:
    assert fold(written) == expected
    assert fold(written) == " ".join(tokens(written))
    assert polarity_of(written) is polarity_of(expected)


def test_every_table_key_is_already_folded() -> None:
    assert {fold(key) for key in TABLE} == set(TABLE)
