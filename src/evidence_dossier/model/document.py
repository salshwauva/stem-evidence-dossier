"""Source content: fetched documents and their sections (plan sections 12 and 13)."""

from datetime import datetime

from evidence_dossier.model.base import FrozenModel
from evidence_dossier.model.enums import SectionType, SourceLevel


class SourceDocument(FrozenModel):
    """One version of the text that is available for a research work (plan sections 12 and 46).

    A change to the text is a new version. The version number and the content
    hash keep evidence offsets reproducible.
    """

    id: str
    research_work_id: str
    version: int
    source_level: SourceLevel
    source_format: str
    raw_text: str
    content_sha256: str
    fetched_at: datetime


class Section(FrozenModel):
    """A part of a source document. Evidence span offsets point into its text."""

    id: str
    document_id: str
    ordinal: int
    section_type: SectionType
    heading: str | None = None
    text: str
