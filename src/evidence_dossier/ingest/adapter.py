"""The common source interface that every literature adapter implements (plan section 29).

The interface keeps the pipeline free of PubMed. An adapter turns one source
API into research works and fetched text. It never writes to the store.
"""

from typing import Protocol

from evidence_dossier.model import FrozenModel, ResearchWork, SourceLevel


class SourceHit(FrozenModel):
    """One search result. The identifier is the value that fetch_metadata accepts."""

    source: str
    identifier: str
    title: str | None = None


class FetchedText(FrozenModel):
    """The content that a source returned for one work, before section parsing.

    source_format names the syntax of the text: "jats_xml" for PMC full text
    and "plain_text" for an abstract.
    """

    text: str
    source_level: SourceLevel
    source_format: str


class LiteratureSourceAdapter(Protocol):
    """One literature source (plan section 29)."""

    @property
    def scheme(self) -> str:
        """The identifier scheme that make_work_id receives, such as "pmid" or "arxiv"."""

    def search(self, query: str, limit: int) -> list[SourceHit]:
        """Return at most limit hits for the query, in source order."""

    def fetch_metadata(self, identifier: str) -> ResearchWork:
        """Return the work with this source identifier. Raises LookupError for an unknown one."""

    def fetch_full_text(self, identifier: str) -> FetchedText | None:
        """Return the best content the source offers, or None when it offers nothing."""
