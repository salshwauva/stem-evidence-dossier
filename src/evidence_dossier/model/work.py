"""Bibliographic records: research works, their authors and the links between works."""

from datetime import date

from pydantic import Field

from evidence_dossier.model.base import FrozenModel
from evidence_dossier.model.enums import Domain, WorkLinkRelation


class Author(FrozenModel):
    """An author with the affiliations that the source lists for that author.

    The advanced dossier clusters research groups from these (plan section 42).
    """

    name: str
    affiliations: tuple[str, ...] = ()


class ResearchWork(FrozenModel):
    """A publication or another research artifact (plan section 11)."""

    id: str
    title: str
    domain: Domain
    doi: str | None = None
    abstract: str | None = None
    publication_date: date | None = None
    venue: str | None = None
    # Source order, so the first and senior authors stay identifiable.
    authors: tuple[Author, ...] = ()
    # Identifier scheme to value, for example {"pmid": "90000001"}.
    external_identifiers: dict[str, str] = Field(default_factory=dict)


class WorkLink(FrozenModel):
    """An explicit link between two works, so dossier counts do not inflate (plan section 46).

    It reads as "source relation target", for example a preprint PREPRINT_OF its
    journal article.
    """

    source_work_id: str
    relation: WorkLinkRelation
    target_work_id: str
