"""Literature source adapters, the section parser and the ingestion pipeline.

This package imports model, profiles and store from evidence_dossier and
nothing else. Every network call goes through HttpClient, so tests run on
recorded fixtures.
"""

from evidence_dossier.ingest.adapter import FetchedText, LiteratureSourceAdapter, SourceHit
from evidence_dossier.ingest.domains import PUBMED_DOMAIN, arxiv_category_domain
from evidence_dossier.ingest.http import HttpClient, HttpxClient

__all__ = [
    "PUBMED_DOMAIN",
    "FetchedText",
    "HttpClient",
    "HttpxClient",
    "LiteratureSourceAdapter",
    "SourceHit",
    "arxiv_category_domain",
]
