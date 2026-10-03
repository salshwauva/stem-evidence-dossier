from evidence_dossier.model import Domain, ResultDirection
from evidence_dossier.query import parse_query

RAG_TEXT = (
    "retrieval-augmented generation reduces factual hallucination"
    " compared with the same model without retrieval"
)
MAPT_TEXT = "MAPT knockdown increases neuronal survival compared with a scrambled control"


def test_parses_the_computer_science_demo_proposition() -> None:
    proposition = parse_query(RAG_TEXT, domain=Domain.COMPUTER_SCIENCE)

    assert proposition.subject == "retrieval-augmented generation"
    assert proposition.relationship == "reduces"
    assert proposition.measurement == "factual hallucination"
    assert proposition.comparator == "the same model without retrieval"
    assert proposition.expected_direction is ResultDirection.DECREASED
    assert proposition.domain is Domain.COMPUTER_SCIENCE
    assert proposition.text == RAG_TEXT
    assert any(
        note.startswith("relationship: matched 'reduces'") for note in proposition.parse_notes
    )
    assert "comparator: split on 'compared with'" in proposition.parse_notes


def test_parses_the_biology_demo_proposition() -> None:
    proposition = parse_query(MAPT_TEXT)

    assert proposition.subject == "mapt knockdown"
    assert proposition.relationship == "increases"
    assert proposition.measurement == "neuronal survival"
    assert proposition.comparator == "a scrambled control"
    assert proposition.expected_direction is ResultDirection.INCREASED
    assert proposition.domain is None
    assert "domain: none given, so retrieval searches every domain" in proposition.parse_notes


def test_parses_a_question_with_no_comparator() -> None:
    proposition = parse_query("Does prompt caching reduce latency?")

    assert proposition.subject == "prompt caching"
    assert proposition.measurement == "latency"
    assert proposition.comparator is None
    assert proposition.expected_direction is ResultDirection.DECREASED
    assert "question: dropped the leading question word" in proposition.parse_notes
    assert "comparator: no comparator marker found" in proposition.parse_notes


def test_negated_and_unknown_relationships() -> None:
    unchanged = parse_query("SIRT1 overexpression does not change mitochondrial density")
    unknown = parse_query("quantum foam warps spacetime")

    assert unchanged.expected_direction is ResultDirection.UNCHANGED
    assert unchanged.measurement == "mitochondrial density"
    assert unknown.relationship == "unknown"
    assert unknown.subject == "quantum foam warps spacetime"
    assert unknown.expected_direction is None


def test_each_parse_gets_its_own_id_and_the_same_fields() -> None:
    first = parse_query(RAG_TEXT)
    second = parse_query(RAG_TEXT)

    assert first.id != second.id
    assert first.model_dump(exclude={"id"}) == second.model_dump(exclude={"id"})
