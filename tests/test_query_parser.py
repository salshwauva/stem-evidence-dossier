from collections.abc import Iterator

import pytest

from evidence_dossier.model import Domain, ResultDirection
from evidence_dossier.query import parse_query, search_evidence
from evidence_dossier.query.parser import RULES_NOTE, DeterministicQueryParser, QueryParser
from evidence_dossier.store import Store
from tests.query_corpus import retrieval_papers, seed

RAG_TEXT = (
    "retrieval-augmented generation reduces factual hallucination"
    " compared with the same model without retrieval"
)
MAPT_TEXT = "MAPT knockdown increases neuronal survival compared with a scrambled control"


@pytest.fixture
def store() -> Iterator[Store]:
    with Store(":memory:") as opened:
        seed(opened, retrieval_papers())
        yield opened


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


@pytest.mark.parametrize("verb", ["increases", "raises", "boosts"])
def test_the_increase_verbs_give_one_relationship(verb: str) -> None:
    proposition = parse_query(f"caffeine {verb} alertness")

    assert proposition.subject == "caffeine"
    assert proposition.relationship == "increases"
    assert proposition.measurement == "alertness"
    assert proposition.expected_direction is ResultDirection.INCREASED


@pytest.mark.parametrize("verb", ["reduces", "decreases", "lowers", "cuts"])
def test_the_decrease_verbs_give_one_relationship(verb: str) -> None:
    proposition = parse_query(f"caffeine {verb} alertness")

    assert proposition.subject == "caffeine"
    assert proposition.relationship == "reduces"
    assert proposition.measurement == "alertness"
    assert proposition.expected_direction is ResultDirection.DECREASED


@pytest.mark.parametrize("verb", ["improves", "enhances"])
def test_the_improve_verbs_give_one_relationship(verb: str) -> None:
    proposition = parse_query(f"caffeine {verb} alertness")

    assert proposition.relationship == "improves"
    assert proposition.expected_direction is ResultDirection.IMPROVED


@pytest.mark.parametrize("verb", ["worsens", "degrades", "harms"])
def test_the_worsen_verbs_give_one_relationship(verb: str) -> None:
    proposition = parse_query(f"caffeine {verb} alertness")

    assert proposition.relationship == "worsens"
    assert proposition.expected_direction is ResultDirection.WORSENED


@pytest.mark.parametrize(
    ("text", "measurement"),
    [
        ("vitamin D supplementation has no effect on fracture risk", "fracture risk"),
        ("the coating shows no change in corrosion rate", "corrosion rate"),
        ("the coating does not change corrosion rate", "corrosion rate"),
        ("the coating does not affect corrosion rate", "corrosion rate"),
    ],
)
def test_no_effect_and_no_change_give_one_relationship(text: str, measurement: str) -> None:
    proposition = parse_query(text)

    assert proposition.relationship == "no change"
    assert proposition.measurement == measurement
    assert proposition.expected_direction is ResultDirection.UNCHANGED


def test_outperform_names_the_comparator_before_the_measurement() -> None:
    proposition = parse_query(
        "Do sparse mixture-of-experts models outperform dense models on downstream accuracy?"
    )

    assert proposition.subject == "sparse mixture-of-experts models"
    assert proposition.relationship == "outperforms"
    assert proposition.comparator == "dense models"
    assert proposition.measurement == "downstream accuracy"
    assert proposition.expected_direction is ResultDirection.IMPROVED


def test_underperform_names_the_comparator_before_the_measurement() -> None:
    proposition = parse_query(
        "lithium iron phosphate cells underperform NMC cells on energy density"
    )

    assert proposition.subject == "lithium iron phosphate cells"
    assert proposition.relationship == "underperforms"
    assert proposition.comparator == "nmc cells"
    assert proposition.measurement == "energy density"
    assert proposition.expected_direction is ResultDirection.WORSENED


@pytest.mark.parametrize(
    ("verb", "label"),
    [
        ("reduce", "does not reduce"),
        ("increase", "does not increase"),
        ("improve", "does not improve"),
        ("worsen", "does not worsen"),
    ],
)
def test_a_negated_verb_never_parses_as_the_plain_verb(verb: str, label: str) -> None:
    proposition = parse_query(f"quantization does not {verb} accuracy")

    assert proposition.subject == "quantization"
    assert proposition.relationship == label
    assert proposition.measurement == "accuracy"
    assert proposition.expected_direction is None
    assert any(note.startswith("negation:") for note in proposition.parse_notes)


@pytest.mark.parametrize(
    "text",
    [
        "prompt caching cuts median latency compared with uncached requests",
        "prompt caching cuts median latency compared to uncached requests",
        "prompt caching cuts median latency versus uncached requests",
        "prompt caching cuts median latency vs uncached requests",
        "prompt caching cuts median latency vs. uncached requests",
        "prompt caching cuts median latency relative to uncached requests",
        "prompt caching cuts median latency against uncached requests",
        "prompt caching cuts median latency over uncached requests",
        "prompt caching cuts median latency further than uncached requests",
    ],
)
def test_every_comparator_phrasing_splits_the_measurement_from_the_comparator(text: str) -> None:
    proposition = parse_query(text)

    assert proposition.subject == "prompt caching"
    assert proposition.measurement == "median latency"
    assert proposition.comparator == "uncached requests"


@pytest.mark.parametrize("word", ["does", "do", "is", "are", "can", "whether", ""])
def test_every_question_form_gives_the_same_proposition(word: str) -> None:
    text = f"{word} prompt caching cuts median latency".strip()

    proposition = parse_query(f"{text}?" if word else text)

    assert proposition.subject == "prompt caching"
    assert proposition.relationship == "reduces"
    assert proposition.measurement == "median latency"
    dropped = "question: dropped the leading question word" in proposition.parse_notes
    assert dropped is bool(word)


def test_the_measurement_stops_at_the_context_that_follows_it() -> None:
    proposition = parse_query(
        "Does metformin lower fasting glucose in type 2 diabetes compared with placebo?"
    )

    assert proposition.subject == "metformin"
    assert proposition.measurement == "fasting glucose"
    assert proposition.comparator == "placebo"
    assert any(note.startswith("measurement: cut the context") for note in proposition.parse_notes)


def test_the_measurement_drops_a_quantity_tail() -> None:
    proposition = parse_query("Prompt caching cut median latency by 41%.")

    assert proposition.subject == "prompt caching"
    assert proposition.measurement == "median latency"


def test_the_first_relationship_verb_in_the_text_wins() -> None:
    proposition = parse_query("the new scheduler increases throughput and reduces cost")

    assert proposition.subject == "new scheduler"
    assert proposition.relationship == "increases"
    assert proposition.measurement == "throughput and reduces cost"


def test_the_subject_drops_a_leading_article_and_a_trailing_adverb() -> None:
    proposition = parse_query("The new index significantly reduces query latency")

    assert proposition.subject == "new index"
    assert proposition.measurement == "query latency"


def test_the_deterministic_parser_wraps_the_rules() -> None:
    parser: QueryParser = DeterministicQueryParser()

    through_protocol = parser.parse(RAG_TEXT, domain=Domain.COMPUTER_SCIENCE)

    direct = parse_query(RAG_TEXT, domain=Domain.COMPUTER_SCIENCE)
    assert through_protocol.model_dump(exclude={"id"}) == direct.model_dump(exclude={"id"})
    assert RULES_NOTE in through_protocol.parse_notes


def test_the_default_search_path_uses_the_deterministic_parser(store: Store) -> None:
    """The pipeline parses with the rules, and no model call sits under a search."""
    results = search_evidence(store, RAG_TEXT, domain=Domain.COMPUTER_SCIENCE)

    expected = parse_query(RAG_TEXT, domain=Domain.COMPUTER_SCIENCE)
    assert results.proposition.model_dump(exclude={"id"}) == expected.model_dump(exclude={"id"})
    assert RULES_NOTE in results.proposition.parse_notes
