"""The section parser: fetched text to ordered Section records (plan section 13).

Evidence offsets point into section text, so the text must stay exact and
stable. The parser keeps the character data of the source as it is. The only
whitespace change is one strip of the leading and trailing whitespace of each
paragraph, and paragraphs of one section join with one blank line. A second
parse of the same input gives the same sections, and a passage of the source
sits at the same offsets in the same section.
"""

import xml.etree.ElementTree as ET
from collections.abc import Iterator

from evidence_dossier.ingest.adapter import FetchedText
from evidence_dossier.ingest.xml import parse_xml
from evidence_dossier.model import Section, SectionType, make_section_id

JATS_FORMAT = "jats_xml"

# Lower-case heading to section type. A heading that starts with a numeral,
# such as "2. Methods", matches after the numeral is removed.
HEADING_TYPES: dict[str, SectionType] = {
    "abstract": SectionType.ABSTRACT,
    "introduction": SectionType.INTRODUCTION,
    "background": SectionType.BACKGROUND,
    "methods": SectionType.METHODS,
    "materials and methods": SectionType.METHODS,
    "experimental setup": SectionType.METHODS,
    "experiments": SectionType.EXPERIMENT,
    "results": SectionType.RESULTS,
    "evaluation": SectionType.EVALUATION,
    "benchmarks": SectionType.EVALUATION,
    "discussion": SectionType.DISCUSSION,
    "conclusion": SectionType.CONCLUSION,
    "conclusions": SectionType.CONCLUSION,
    "appendix": SectionType.APPENDIX,
}

_PARAGRAPH_SEPARATOR = "\n\n"


def section_type_for_heading(heading: str) -> SectionType:
    """Return the section type for a heading, or OTHER when the heading table has no entry."""
    words = heading.lower().strip().rstrip(":.").split()
    if words and words[0].rstrip(".").replace(".", "").isdigit():
        words = words[1:]
    key = " ".join(words)
    if key in HEADING_TYPES:
        return HEADING_TYPES[key]
    if key.startswith("appendix"):
        return SectionType.APPENDIX
    return SectionType.OTHER


class SectionParser:
    """Turns fetched text into the ordered sections of one document."""

    def parse(self, fetched: FetchedText, document_id: str) -> list[Section]:
        """Return the sections of the document, with ordinals from 0 in document order.

        JATS XML gives one section per abstract, per <sec> at any depth, per
        figure caption, per table and per appendix. A nested <sec> whose
        heading maps to OTHER takes the type of its parent, so "Cell culture"
        under "Materials and Methods" is METHODS. A <sec> with no paragraph of
        its own, such as a container of subsections, gives no section. Any
        other format is one ABSTRACT section that holds the whole text. Empty
        text gives no section.
        """
        if fetched.source_format == JATS_FORMAT:
            parts = list(_jats_parts(parse_xml(fetched.text)))
        else:
            parts = [(SectionType.ABSTRACT, None, fetched.text.strip())]
        return [
            Section(
                id=make_section_id(document_id, ordinal),
                document_id=document_id,
                ordinal=ordinal,
                section_type=section_type,
                heading=heading,
                text=text,
            )
            for ordinal, (section_type, heading, text) in enumerate(
                part for part in parts if part[2]
            )
        ]


def _jats_parts(root: ET.Element) -> Iterator[tuple[SectionType, str | None, str]]:
    article = root if root.tag == "article" else root.find("article")
    if article is None:
        return
    for abstract in article.iterfind("front/article-meta/abstract"):
        yield SectionType.ABSTRACT, "Abstract", _paragraphs(abstract)
    body = article.find("body")
    if body is not None:
        yield from _blocks(body)
    for appendix in article.iterfind("back/app-group/app"):
        heading = _text(appendix.find("title")) or "Appendix"
        yield SectionType.APPENDIX, heading, _paragraphs(appendix)


def _blocks(
    parent: ET.Element, inherited: SectionType = SectionType.OTHER
) -> Iterator[tuple[SectionType, str | None, str]]:
    """Yield the sections, figure captions and tables under a body or a sec, in document order."""
    for child in parent:
        if child.tag == "sec":
            heading = _text(child.find("title"))
            section_type = section_type_for_heading(heading)
            if section_type == SectionType.OTHER:
                section_type = inherited
            yield section_type, heading or None, _paragraphs(child)
            yield from _blocks(child, section_type)
        elif child.tag == "fig":
            yield SectionType.FIGURE_CAPTION, _text(child.find("label")) or None, _caption(child)
        elif child.tag == "table-wrap":
            yield SectionType.TABLE, _text(child.find("label")) or None, _table(child)


def _paragraphs(element: ET.Element) -> str:
    return _PARAGRAPH_SEPARATOR.join(
        text for text in (_text(paragraph) for paragraph in element.iterfind("p")) if text
    )


def _caption(element: ET.Element) -> str:
    caption = element.find("caption")
    return "" if caption is None else _paragraphs(caption)


def _table(element: ET.Element) -> str:
    rows = [
        "\t".join(_text(cell) for cell in row if cell.tag in ("th", "td"))
        for row in element.iter("tr")
    ]
    return _PARAGRAPH_SEPARATOR.join(part for part in (_caption(element), "\n".join(rows)) if part)


def _text(element: ET.Element | None) -> str:
    """Return the character data of an element and its descendants, with the outer whitespace removed."""
    return "" if element is None else "".join(element.itertext()).strip()
