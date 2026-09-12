"""The arXiv adapter (plan section 30).

Metadata comes from the arXiv API Atom feed. arXiv offers no structured full
text: the PDF and the LaTeX source need a converter that this increment does
not have. fetch_full_text therefore returns the abstract at source level
ABSTRACT_ONLY, and a later increment can replace it with a PDF path.
"""

import xml.etree.ElementTree as ET
from datetime import date

from evidence_dossier.ingest.adapter import FetchedText, SourceHit
from evidence_dossier.ingest.domains import arxiv_category_domain
from evidence_dossier.ingest.http import HttpClient
from evidence_dossier.ingest.xml import parse_xml
from evidence_dossier.model import Author, Domain, ResearchWork, SourceLevel, make_work_id

QUERY_URL = "https://export.arxiv.org/api/query"

_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivAdapter:
    """Literature source adapter for arXiv metadata, with the abstract as the only text."""

    scheme = "arxiv"

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def search(self, query: str, limit: int) -> list[SourceHit]:
        body = self._http.get(
            QUERY_URL, {"search_query": f"all:{query}", "max_results": str(limit), "start": "0"}
        )
        root = parse_xml(body)
        return [
            SourceHit(
                source="arxiv",
                identifier=_identifier(entry),
                title=_title(entry),
            )
            for entry in root.iterfind("atom:entry", _NS)
        ][:limit]

    def fetch_metadata(self, identifier: str) -> ResearchWork:
        entry = self._entry(identifier)
        primary = entry.find("arxiv:primary_category", _NS)
        category = None if primary is None else primary.get("term")
        doi = _text(entry.find("arxiv:doi", _NS)) or None
        identifiers = {"arxiv": identifier}
        if doi is not None:
            identifiers["doi"] = doi
        published = _text(entry.find("atom:published", _NS))
        return ResearchWork(
            id=make_work_id(self.scheme, identifier),
            title=_title(entry),
            domain=Domain.OTHER_STEM if category is None else arxiv_category_domain(category),
            doi=doi,
            abstract=_text(entry.find("atom:summary", _NS)) or None,
            publication_date=date.fromisoformat(published[:10]) if published else None,
            venue=_text(entry.find("arxiv:journal_ref", _NS)) or "arXiv",
            authors=tuple(
                Author(
                    name=_text(author.find("atom:name", _NS)),
                    affiliations=tuple(
                        _text(affiliation)
                        for affiliation in author.iterfind("arxiv:affiliation", _NS)
                    ),
                )
                for author in entry.iterfind("atom:author", _NS)
            ),
            external_identifiers=identifiers,
        )

    def fetch_full_text(self, identifier: str) -> FetchedText | None:
        """Return the abstract as ABSTRACT_ONLY plain text, or None when the entry has none."""
        abstract = _text(self._entry(identifier).find("atom:summary", _NS))
        if not abstract:
            return None
        return FetchedText(
            text=abstract, source_level=SourceLevel.ABSTRACT_ONLY, source_format="plain_text"
        )

    def _entry(self, identifier: str) -> ET.Element:
        body = self._http.get(QUERY_URL, {"id_list": identifier, "max_results": "1"})
        entry = parse_xml(body).find("atom:entry", _NS)
        if entry is None:
            raise LookupError(f"arXiv has no entry with identifier {identifier}")
        return entry


def _text(element: ET.Element | None) -> str:
    """Return the text of an element with the outer whitespace removed. Inner newlines stay."""
    return "" if element is None else "".join(element.itertext()).strip()


def _title(entry: ET.Element) -> str:
    """Return the title on one line. The feed wraps long titles with a newline and spaces."""
    return " ".join(_text(entry.find("atom:title", _NS)).split())


def _identifier(entry: ET.Element) -> str:
    """Return the arXiv identifier without the version, from an entry id URL."""
    url = _text(entry.find("atom:id", _NS))
    identifier = url.rsplit("/abs/", 1)[-1]
    stem, sep, version = identifier.rpartition("v")
    return stem if sep and version.isdigit() else identifier
