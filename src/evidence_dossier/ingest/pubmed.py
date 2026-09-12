"""The PubMed and PMC adapter (plan section 30).

Metadata comes from the E-utilities: esearch for identifiers and efetch for
one PubmedArticle record. Full text comes from PMC: the id converter maps a
PMID to a PMCID, the OA web service reports the license, and efetch on the pmc
database returns the JATS XML. A work outside PMC open access, or one under a
license that the allow list does not hold, gets no full text, and the caller
falls back to the abstract (plan section 51).
"""

import json
import xml.etree.ElementTree as ET
from datetime import date

from evidence_dossier.ingest.adapter import FetchedText, SourceHit
from evidence_dossier.ingest.domains import PUBMED_DOMAIN
from evidence_dossier.ingest.http import HttpClient
from evidence_dossier.ingest.xml import parse_xml
from evidence_dossier.model import Author, ResearchWork, SourceLevel, make_work_id

EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_URL}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_URL}/efetch.fcgi"
IDCONV_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"

# The licenses that let the store keep and serve the article body. CC BY-NC and
# CC BY-ND stay out: the dossier is a public evidence store, so it redistributes
# the stored full text, and those two terms restrict redistribution. NC bars
# commercial reuse and ND bars a modified form, and a section split plus a
# quoted span is a modified form. A comparison folds case and hyphens, so
# "cc-by" and "CC-BY" match "CC BY".
FULL_TEXT_LICENSES = frozenset({"ccby", "cc0"})

_MONTHS = {
    name: number
    for number, name in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
        start=1,
    )
}


class PubMedAdapter:
    """Literature source adapter for PubMed metadata and PMC open access full text."""

    scheme = "pmid"

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def search(self, query: str, limit: int) -> list[SourceHit]:
        """Return PMIDs for the query. esearch returns no titles, so each hit has none."""
        body = self._http.get(
            ESEARCH_URL, {"db": "pubmed", "term": query, "retmax": str(limit), "retmode": "xml"}
        )
        root = parse_xml(body)
        return [
            SourceHit(source="pubmed", identifier=element.text.strip())
            for element in root.iterfind("IdList/Id")
            if element.text
        ][:limit]

    def fetch_metadata(self, identifier: str) -> ResearchWork:
        body = self._http.get(EFETCH_URL, {"db": "pubmed", "id": identifier, "retmode": "xml"})
        article = parse_xml(body).find("PubmedArticle")
        if article is None:
            raise LookupError(f"PubMed has no article with PMID {identifier}")
        identifiers = {"pmid": identifier}
        for article_id in article.iterfind("PubmedData/ArticleIdList/ArticleId"):
            id_type = article_id.get("IdType")
            if id_type in ("doi", "pmc") and article_id.text:
                identifiers[id_type] = article_id.text.strip()
        abstract_parts = [
            _text(part)
            for part in article.iterfind("MedlineCitation/Article/Abstract/AbstractText")
        ]
        return ResearchWork(
            id=make_work_id(self.scheme, identifier),
            title=_text(article.find("MedlineCitation/Article/ArticleTitle")).rstrip("."),
            domain=PUBMED_DOMAIN,
            doi=identifiers.get("doi"),
            abstract="\n\n".join(part for part in abstract_parts if part) or None,
            publication_date=_pub_date(
                article.find("MedlineCitation/Article/Journal/JournalIssue/PubDate")
            ),
            venue=_text(article.find("MedlineCitation/Article/Journal/Title")) or None,
            authors=tuple(
                _author(element)
                for element in article.iterfind("MedlineCitation/Article/AuthorList/Author")
            ),
            external_identifiers=identifiers,
        )

    def fetch_full_text(self, identifier: str) -> FetchedText | None:
        """Return the PMC JATS XML, or None when the license does not permit the full text."""
        records = json.loads(self._http.get(IDCONV_URL, {"ids": identifier, "format": "json"}))
        pmcid = next(
            (record.get("pmcid") for record in records.get("records", []) if record.get("pmcid")),
            None,
        )
        if pmcid is None:
            return None
        license_name = self._permitted_license(pmcid)
        if license_name is None:
            return None
        body = self._http.get(EFETCH_URL, {"db": "pmc", "id": pmcid, "retmode": "xml"})
        if parse_xml(body).find("article/body") is None:
            return None
        return FetchedText(
            text=body.decode(),
            source_level=SourceLevel.FULL_TEXT,
            source_format="jats_xml",
            license=license_name,
        )

    def _permitted_license(self, pmcid: str) -> str | None:
        """Return the OA service license of the PMCID when the allow list holds it, else None.

        The service answers with an error element for an article outside the
        open access subset, and the method then returns None.
        """
        record = parse_xml(self._http.get(OA_URL, {"id": pmcid})).find("records/record")
        if record is None:
            return None
        license_name = (record.get("license") or "").strip()
        folded = license_name.lower().replace("-", "").replace(" ", "")
        return license_name if folded in FULL_TEXT_LICENSES else None


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext()).strip()


def _author(element: ET.Element) -> Author:
    collective = _text(element.find("CollectiveName"))
    name = collective or " ".join(
        part for part in (_text(element.find("ForeName")), _text(element.find("LastName"))) if part
    )
    affiliations = tuple(
        _text(affiliation) for affiliation in element.iterfind("AffiliationInfo/Affiliation")
    )
    return Author(name=name, affiliations=affiliations)


def _pub_date(element: ET.Element | None) -> date | None:
    year = _text(None if element is None else element.find("Year"))
    if not year:
        return None
    month_text = _text(None if element is None else element.find("Month")).lower()
    month = _MONTHS.get(month_text[:3]) or (int(month_text) if month_text.isdigit() else 1)
    day_text = _text(None if element is None else element.find("Day"))
    return date(int(year), month, int(day_text) if day_text.isdigit() else 1)
