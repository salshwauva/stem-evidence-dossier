import pytest

from evidence_dossier.ingest import FetchedText, SectionParser, section_type_for_heading
from evidence_dossier.model import SectionType, SourceLevel
from tests.recorded_http import FIXTURES_DIR


def jats_fixture() -> FetchedText:
    text = (FIXTURES_DIR / "pmc_efetch_PMC9900001.xml").read_text()
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


def test_plain_text_is_one_abstract_section_with_only_the_ends_stripped() -> None:
    fetched = FetchedText(
        text="  Line one.\n\n  Line two.  ",
        source_level=SourceLevel.ABSTRACT_ONLY,
        source_format="plain_text",
    )
    sections = SectionParser().parse(fetched, "doc")
    assert len(sections) == 1
    assert sections[0].section_type == SectionType.ABSTRACT
    assert sections[0].heading is None
    assert sections[0].text == "Line one.\n\n  Line two."


def test_empty_text_gives_no_section() -> None:
    fetched = FetchedText(
        text="", source_level=SourceLevel.METADATA_ONLY, source_format="plain_text"
    )
    assert SectionParser().parse(fetched, "doc") == []
