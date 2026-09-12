"""Literature source adapters, the section parser and the ingestion pipeline.

This package imports model, profiles and store from evidence_dossier and
nothing else. Every network call goes through HttpClient, so tests run on
recorded fixtures.
"""

from evidence_dossier.ingest.adapter import FetchedText, LiteratureSourceAdapter, SourceHit
from evidence_dossier.ingest.arxiv import ArxivAdapter
from evidence_dossier.ingest.domains import PUBMED_DOMAIN, arxiv_category_domain, pubmed_domain
from evidence_dossier.ingest.http import HttpClient, HttpxClient
from evidence_dossier.ingest.pipeline import IngestResult, ingest_work
from evidence_dossier.ingest.pubmed import PubMedAdapter
from evidence_dossier.ingest.sections import HEADING_TYPES, SectionParser, section_type_for_heading

__all__ = [
    "HEADING_TYPES",
    "PUBMED_DOMAIN",
    "ArxivAdapter",
    "FetchedText",
    "HttpClient",
    "HttpxClient",
    "IngestResult",
    "LiteratureSourceAdapter",
    "PubMedAdapter",
    "SectionParser",
    "SourceHit",
    "arxiv_category_domain",
    "pubmed_domain",
    "ingest_work",
    "section_type_for_heading",
]
