import pytest

from evidence_dossier.ingest import FetchedText, SectionParser, section_type_for_heading
from evidence_dossier.model import SectionType, SourceLevel
from tests.recorded_http import FIXTURES_DIR


def jats_fixture() -> FetchedText:
    text = (FIXTURES_DIR / "pmc_efetch_PMC99900001.xml").read_text()
    return FetchedText(text=text, source_level=SourceLevel.FULL_TEXT, source_format="jats_xml")


def jats(front: str = "", body: str = "") -> FetchedText:
    """Wrap invented article-meta and body markup in the eFetch shape of one PMC article."""
    text = (
        "<pmc-articleset><article><front><article-meta>"
        f"{front}</article-meta></front><body>{body}</body></article></pmc-articleset>"
    )
    return FetchedText(text=text, source_level=SourceLevel.FULL_TEXT, source_format="jats_xml")


@pytest.mark.parametrize(
    ("heading", "section_type"),
    [
        ("Abstract", SectionType.ABSTRACT),
        ("Introduction", SectionType.INTRODUCTION),
        ("1. Introduction", SectionType.INTRODUCTION),
        ("Background", SectionType.BACKGROUND),
        ("Methods", SectionType.METHODS),
        ("Materials and Methods", SectionType.METHODS),
        ("Experimental Setup", SectionType.METHODS),
        ("Experiments", SectionType.EXPERIMENT),
        ("RESULTS", SectionType.RESULTS),
        ("Evaluation", SectionType.EVALUATION),
        ("Benchmarks", SectionType.EVALUATION),
        ("Discussion", SectionType.DISCUSSION),
        ("Conclusion", SectionType.CONCLUSION),
        ("Conclusions", SectionType.CONCLUSION),
        ("Appendix", SectionType.APPENDIX),
        ("Appendix B", SectionType.APPENDIX),
        ("Cell culture", SectionType.OTHER),
        ("", SectionType.OTHER),
    ],
)
def test_heading_maps_to_section_type(heading: str, section_type: SectionType) -> None:
    assert section_type_for_heading(heading) == section_type


def test_jats_gives_one_section_per_block_in_document_order() -> None:
    """The "Materials and Methods" container has no paragraph of its own, so it gives no section."""
    sections = SectionParser().parse(jats_fixture(), "doc")
    assert [section.ordinal for section in sections] == list(range(len(sections)))
    assert [section.id for section in sections][:2] == ["doc_s0", "doc_s1"]
    assert [(section.section_type, section.heading) for section in sections] == [
        (SectionType.ABSTRACT, "Abstract"),
        (SectionType.INTRODUCTION, "Introduction"),
        (SectionType.METHODS, "Cell culture"),
        (SectionType.METHODS, "Knockdown"),
        (SectionType.RESULTS, "Results"),
        (SectionType.FIGURE_CAPTION, "Figure 1"),
        (SectionType.TABLE, "Table 1"),
        (SectionType.DISCUSSION, "Discussion"),
        (SectionType.CONCLUSION, "Conclusions"),
        (SectionType.APPENDIX, "Appendix A"),
    ]


def test_jats_section_text_keeps_inline_markup_text_and_joins_paragraphs() -> None:
    sections = {
        section.heading: section for section in SectionParser().parse(jats_fixture(), "doc")
    }
    assert sections["Introduction"].text == (
        "The test dementia model accumulates tau in cortical neurons. Earlier work in this"
        " model measured survival over 7 days.\n\n"
        "This study extends the window to 14 days and adds a scrambled control."
    )
    assert sections["Knockdown"].text.startswith("An antisense oligonucleotide against MAPT was")
    assert sections["Table 1"].text == (
        "Survival by condition.\n\n"
        "Condition\tSurvival (%)\nMAPT knockdown\t84\nScrambled control\t52"
    )
    assert sections["Figure 1"].text == (
        "Neuronal survival on day 14 for MAPT knockdown and scrambled control."
    )


def test_jats_offsets_are_stable_across_parses() -> None:
    passage = "raised neuronal survival by 32%"
    first = SectionParser().parse(jats_fixture(), "doc")[4]
    second = SectionParser().parse(jats_fixture(), "doc")[4]
    start = first.text.index(passage)
    assert second.text[start : start + len(passage)] == passage


def test_plain_text_is_one_abstract_section_with_one_space_inside_each_paragraph() -> None:
    """A hard wrap inside a sentence becomes a space. A blank line stays a paragraph break."""
    fetched = FetchedText(
        text="  Line one wraps\n  here.\n \n  Line two.  ",
        source_level=SourceLevel.ABSTRACT_ONLY,
        source_format="plain_text",
    )
    sections = SectionParser().parse(fetched, "doc")
    assert len(sections) == 1
    assert sections[0].section_type == SectionType.ABSTRACT
    assert sections[0].heading is None
    assert sections[0].text == "Line one wraps here.\n\nLine two."


def test_structured_abstract_keeps_the_paragraphs_of_its_parts() -> None:
    fetched = jats(
        front=(
            "<abstract><title>Abstract</title>"
            "<sec><title>Background</title><p>Tau builds up in the test model.</p></sec>"
            "<sec><title>Results</title><p>Knockdown raised survival by 32%.</p></sec>"
            "</abstract>"
        )
    )
    (section,) = SectionParser().parse(fetched, "doc")
    assert (section.section_type, section.heading) == (SectionType.ABSTRACT, "Abstract")
    assert section.text == "Tau builds up in the test model.\n\nKnockdown raised survival by 32%."


def test_a_typed_abstract_gets_its_type_in_the_heading() -> None:
    fetched = jats(
        front=(
            "<abstract><p>Knockdown raised survival by 32%.</p></abstract>"
            '<abstract abstract-type="graphical"><p>A test graphical summary.</p></abstract>'
        )
    )
    sections = SectionParser().parse(fetched, "doc")
    assert [(section.section_type, section.heading) for section in sections] == [
        (SectionType.ABSTRACT, "Abstract"),
        (SectionType.ABSTRACT, "Abstract (graphical)"),
    ]


def test_list_items_count_as_paragraphs() -> None:
    fetched = jats(
        body=(
            "<sec><title>Methods</title><p>Two groups took part.</p>"
            "<list><list-item><p>Knockdown mice.</p></list-item>"
            "<list-item><p>Scrambled control mice.</p></list-item></list></sec>"
        )
    )
    (section,) = SectionParser().parse(fetched, "doc")
    assert section.text == "Two groups took part.\n\nKnockdown mice.\n\nScrambled control mice."


def test_paragraphs_directly_under_the_body_give_one_section_first() -> None:
    fetched = jats(
        body=(
            "<p>A letter with no section heading.</p>"
            "<sec><title>Methods</title><p>Two groups took part.</p></sec>"
        )
    )
    sections = SectionParser().parse(fetched, "doc")
    assert [(section.section_type, section.heading, section.text) for section in sections] == [
        (SectionType.OTHER, None, "A letter with no section heading."),
        (SectionType.METHODS, "Methods", "Two groups took part."),
    ]


def test_a_thin_space_at_the_edge_of_a_table_cell_stays() -> None:
    fetched = jats(
        body=(
            "<table-wrap><label>Table 1</label><table><tr><td>\u2009-4.2</td><td>12\u2009</td>"
            "</tr></table></table-wrap>"
        )
    )
    (section,) = SectionParser().parse(fetched, "doc")
    assert section.text == "\u2009-4.2\t12\u2009"


def test_a_space_run_between_inline_elements_becomes_one_space() -> None:
    """The formatting newline between two inline elements reads as a space. A thin space stays."""
    fetched = jats(
        body=(
            "<sec><title>Methods</title><p>Mice carrying <italic>Ttbk2</italic>\n"
            "<sup>fl/fl</sup> alleles were tested at 20\u2009min intervals in AD.\n"
            "<sup><xref>1</xref></sup></p></sec>"
        )
    )
    (section,) = SectionParser().parse(fetched, "doc")
    assert section.text == (
        "Mice carrying Ttbk2 fl/fl alleles were tested at 20\u2009min intervals in AD. 1"
    )


def test_empty_text_gives_no_section() -> None:
    fetched = FetchedText(
        text="", source_level=SourceLevel.METADATA_ONLY, source_format="plain_text"
    )
    assert SectionParser().parse(fetched, "doc") == []
