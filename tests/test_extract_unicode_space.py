"""A reply that copies a no-break space as a plain space still finds its passage."""

import json

from evidence_dossier.extract.validation import ValidationOutcome, validate_response
from evidence_dossier.model import Section
from evidence_dossier.store import Store
from tests.extract_support import add_paper, valid_response

NBSP_TEXT = "The treated group scored 12.5\u00a0percent higher (P\u00a0=\u00a00.001) than controls."


def _reply_quoting(quote: str) -> str:
    data = json.loads(valid_response())
    data["claims"] = data["claims"][:1]
    data["claims"][0]["evidence"] = {
        **data["claims"][0]["evidence"],
        "section_id": "{s}",
        "source_text": quote,
    }
    return json.dumps(data)


def _validate(quote: str, section_text: str = NBSP_TEXT) -> tuple[Section, ValidationOutcome]:
    with Store(":memory:") as store:
        corpus = add_paper(store, "2409.00002", (section_text,))
        section = corpus.sections[0]
        reply = _reply_quoting(quote).replace("{s}", section.id)
        return section, validate_response(reply, corpus.document, corpus.sections)


def test_plain_spaces_match_no_break_spaces_and_the_span_keeps_the_exact_text() -> None:
    section, outcome = _validate("scored 12.5 percent higher (P = 0.001)")
    assert outcome.errors == ()
    (span,) = outcome.spans
    assert span.source_text == "scored 12.5\u00a0percent higher (P\u00a0=\u00a00.001)"
    assert section.text[span.start_offset : span.end_offset] == span.source_text
    assert span.end_offset - span.start_offset == len("scored 12.5 percent higher (P = 0.001)")


def test_an_exact_quote_still_matches_exactly() -> None:
    section, outcome = _validate("scored 12.5\u00a0percent higher")
    assert outcome.errors == ()
    assert outcome.spans[0].source_text == "scored 12.5\u00a0percent higher"


def test_a_quote_that_matches_twice_after_the_space_rule_is_still_ambiguous() -> None:
    twice = "alpha\u00a0beta and alpha\u00a0beta"
    _, outcome = _validate("alpha beta", twice)
    assert outcome.errors
    assert "occurs 2 times" in outcome.errors[0]


def test_a_quote_that_is_absent_stays_an_error() -> None:
    _, outcome = _validate("scored 99 percent higher")
    assert "does not occur" in outcome.errors[0]
