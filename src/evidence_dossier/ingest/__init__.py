"""Literature source adapters, the section parser and the ingestion pipeline.

This package imports model, profiles and store from evidence_dossier and
nothing else. Every network call goes through HttpClient, so tests run on
recorded fixtures.
"""

from evidence_dossier.ingest.adapter import FetchedText, LiteratureSourceAdapter, SourceHit
from evidence_dossier.ingest.arxiv import ArxivAdapter
from evidence_dossier.ingest.domains import PUBMED_DOMAIN, arxiv_category_domain
from evidence_dossier.ingest.http import HttpClient, HttpxClient
from evidence_dossier.ingest.pubmed import PubMedAdapter

__all__ = [
    "PUBMED_DOMAIN",
    "ArxivAdapter",
    "FetchedText",
    "HttpClient",
    "HttpxClient",
    "LiteratureSourceAdapter",
    "PubMedAdapter",
    "SourceHit",
    "arxiv_category_domain",
]
