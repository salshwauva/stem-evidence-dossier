import pytest

from evidence_dossier.model import EvidenceSpan, Section, SectionType

SECTION = Section(
    id="section-results",
    document_id="document-1",
    ordinal=3,
    section_type=SectionType.RESULTS,
    heading="Results",
    text="Retrieval lowered the factual error rate from 18.2% to 11.5% on Benchmark X.",
)
PASSAGE = "factual error rate"
START = SECTION.text.index(PASSAGE)
END = START + len(PASSAGE)
TAIL = SECTION.text[-12:]


def _span(start: int, end: int, source_text: str, section_id: str = SECTION.id) -> EvidenceSpan:
    return EvidenceSpan(
        research_work_id="work-1",
        section_id=section_id,
        start_offset=start,
        end_offset=end,
        source_text=source_text,
    )


def test_exact_span_matches_its_section() -> None:
    assert _span(START, END, PASSAGE).matches(SECTION)


@pytest.mark.parametrize(
    "span",
    [
        _span(START + 1, END + 1, PASSAGE),
        _span(START, END, "factual error rats"),
        _span(START, END, PASSAGE, section_id="section-discussion"),
        # Python slicing clamps an end past the text, so the check must bound it.
        _span(len(SECTION.text) - 12, len(SECTION.text) + 5, TAIL),
        # Negative offsets slice from the end in Python and must not count.
        _span(-12, len(SECTION.text), TAIL),
        _span(START, START, ""),
    ],
    ids=[
        "shifted",
        "text_mismatch",
        "other_section",
        "end_past_text",
        "negative_start",
        "empty",
    ],
)
def test_span_that_does_not_point_at_its_text_is_rejected(span: EvidenceSpan) -> None:
    assert not span.matches(SECTION)
