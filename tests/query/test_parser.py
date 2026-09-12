"""The deterministic parser turns query text into a typed proposition (plan section 34)."""

import pytest

from evidence_dossier.model import Domain, ResultDirection, Term
from evidence_dossier.query import (
    PARSER_VERSION,
    DeterministicQueryParser,
    QueryParseError,
    QueryProposition,
    Relationship,
)

CS_QUERY = (
    "Retrieval-augmented generation reduces factual hallucination "
    "compared with prompting the same model without retrieval."
)
BIOLOGY_QUERY = "MAPT knockdown increases neuronal survival compared with a scrambled control."


def test_parses_the_plan_computer_science_query() -> None:
    parser = DeterministicQueryParser()

    proposition = parser.parse(CS_QUERY, domain=Domain.COMPUTER_SCIENCE)

    assert proposition.subject.original == "Retrieval-augmented generation"
    assert proposition.relationship is Relationship.REDUCES
    assert proposition.measurement.original == "factual hallucination"
    assert proposition.comparator is not None
    assert proposition.comparator.original == "prompting the same model without retrieval"
    assert proposition.expected_direction is ResultDirection.DECREASED
    assert proposition.domain is Domain.COMPUTER_SCIENCE
    assert proposition.parser_version == PARSER_VERSION
    assert proposition.original_text == CS_QUERY


def test_parses_a_biology_query_with_the_same_grammar() -> None:
    parser = DeterministicQueryParser()

    proposition = parser.parse(BIOLOGY_QUERY, domain=Domain.BIOLOGY)

    assert proposition.subject.original == "MAPT knockdown"
    assert proposition.relationship is Relationship.INCREASES
    assert proposition.measurement.original == "neuronal survival"
    assert proposition.comparator is not None
    assert proposition.comparator.original == "a scrambled control"
    assert proposition.expected_direction is ResultDirection.INCREASED


def test_improves_maps_to_the_improved_direction() -> None:
    parser = DeterministicQueryParser()

    proposition = parser.parse("Quantization improves inference latency.")

    assert proposition.relationship is Relationship.IMPROVES
    assert proposition.expected_direction is ResultDirection.IMPROVED
    assert proposition.measurement.original == "inference latency"


def test_canonical_values_come_from_the_injected_canonicalizer() -> None:
    parser = DeterministicQueryParser(canonicalizer=str.upper)

    proposition = parser.parse(CS_QUERY)

    assert proposition.subject.canonical == "RETRIEVAL-AUGMENTED GENERATION"
    assert proposition.measurement.canonical == "FACTUAL HALLUCINATION"


def test_an_absent_comparator_is_unresolved_and_never_guessed() -> None:
    parser = DeterministicQueryParser()

    proposition = parser.parse("Retrieval reduces factual hallucination.")

    assert proposition.comparator is None
    assert proposition.context is None
    assert proposition.method is None
    assert "comparator" in proposition.unresolved_fields
    assert "context" in proposition.unresolved_fields
    assert "method" in proposition.unresolved_fields


def test_an_absent_domain_stays_none() -> None:
    parser = DeterministicQueryParser()

    proposition = parser.parse("Retrieval reduces factual hallucination in a language model.")

    assert proposition.domain is None
    assert "domain" in proposition.unresolved_fields


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "retrieval and hallucination",
        "Retrieval reduces.",
        "reduces factual hallucination",
        "Retrieval affects factual hallucination.",
    ],
)
def test_text_without_a_documented_relation_is_rejected(text: str) -> None:
    parser = DeterministicQueryParser()

    with pytest.raises(QueryParseError):
        parser.parse(text)


def test_the_rejection_message_names_the_documented_relations() -> None:
    parser = DeterministicQueryParser()

    with pytest.raises(QueryParseError) as error:
        parser.parse("Retrieval affects factual hallucination.")

    message = str(error.value)
    assert "increases" in message
    assert "reduces" in message
    assert "improves" in message


def test_a_fallback_parser_runs_only_when_the_rules_fail() -> None:
    calls: list[str] = []

    def fallback(text: str, *, domain: Domain | None = None) -> QueryProposition:
        calls.append(text)
        return QueryProposition(
            original_text=text,
            subject=Term(original="retrieval"),
            relationship=Relationship.REDUCES,
            measurement=Term(original="factual hallucination"),
            expected_direction=ResultDirection.DECREASED,
            parser_version="fallback-test",
        )

    parser = DeterministicQueryParser(fallback=fallback)

    rule_hit = parser.parse(CS_QUERY)
    fallback_hit = parser.parse("Retrieval affects factual hallucination.")

    assert calls == ["Retrieval affects factual hallucination."]
    assert rule_hit.parser_version == PARSER_VERSION
    assert fallback_hit.parser_version == "fallback-test"


def test_a_proposition_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError):
        QueryProposition(
            original_text=CS_QUERY,
            subject=Term(original="retrieval"),
            relationship=Relationship.REDUCES,
            measurement=Term(original="factual hallucination"),
            expected_direction=ResultDirection.DECREASED,
            parser_version=PARSER_VERSION,
            confidence=0.9,  # type: ignore[call-arg]
        )
