"""ingest_work: one identifier from one source into the store (plan sections 31 and 46).

The pipeline fetches the metadata, tries the full text, and falls back to the
abstract and then to metadata alone. It stores the work, one source document
and its sections. The result carries the license of an accepted full text,
which the store does not hold (ADR 0009). A repeat ingestion with the same
text writes nothing. A change to the text writes the next document version,
because evidence offsets of the earlier version must stay valid.
"""

import hashlib
from datetime import datetime

from evidence_dossier.ingest.adapter import FetchedText, LiteratureSourceAdapter
from evidence_dossier.ingest.sections import SectionParser
from evidence_dossier.model import (
    FrozenModel,
    SourceDocument,
    SourceLevel,
    make_document_id,
    make_section_id,
)
from evidence_dossier.store import Store

PLAIN_TEXT_FORMAT = "plain_text"


class IngestResult(FrozenModel):
    """What one ingestion stored, or found in the store already."""

    work_id: str
    document_id: str
    version: int
    source_level: SourceLevel
    section_count: int
    # False when the store held this text already and nothing was written.
    stored: bool
    # The license that permitted the full text, such as "CC BY". None for an
    # abstract and for metadata alone. SourceDocument has no license column, so
    # the license travels on the result instead of into the store (ADR 0009).
    license: str | None = None


def ingest_work(
    store: Store, adapter: LiteratureSourceAdapter, identifier: str, *, fetched_at: datetime
) -> IngestResult:
    """Fetch one work through the adapter and store it with its best available text."""
    work = adapter.fetch_metadata(identifier)
    if store.get_work(work.id) is None:
        store.add_work(work)
    fetched = adapter.fetch_full_text(identifier)
    if fetched is None:
        fetched = _fallback(work.abstract)
    digest = hashlib.sha256(fetched.text.encode()).hexdigest()

    latest = _latest_document(store, work.id)
    if latest is not None and latest.content_sha256 == digest:
        return IngestResult(
            work_id=work.id,
            document_id=latest.id,
            version=latest.version,
            source_level=latest.source_level,
            section_count=_section_count(store, latest.id),
            stored=False,
            license=fetched.license,
        )
    version = 1 if latest is None else latest.version + 1
    document = SourceDocument(
        id=make_document_id(work.id, version),
        research_work_id=work.id,
        version=version,
        source_level=fetched.source_level,
        source_format=fetched.source_format,
        raw_text=fetched.text,
        content_sha256=digest,
        fetched_at=fetched_at,
    )
    sections = SectionParser().parse(fetched, document.id)
    store.add_source_document(document)
    for section in sections:
        store.add_section(section)
    return IngestResult(
        work_id=work.id,
        document_id=document.id,
        version=version,
        source_level=fetched.source_level,
        section_count=len(sections),
        stored=True,
        license=fetched.license,
    )


def _fallback(abstract: str | None) -> FetchedText:
    if abstract:
        return FetchedText(
            text=abstract, source_level=SourceLevel.ABSTRACT_ONLY, source_format=PLAIN_TEXT_FORMAT
        )
    return FetchedText(
        text="", source_level=SourceLevel.METADATA_ONLY, source_format=PLAIN_TEXT_FORMAT
    )


def _latest_document(store: Store, work_id: str) -> SourceDocument | None:
    """Return the highest stored version of the work, by walking the deterministic document IDs."""
    latest = None
    version = 1
    while (document := store.get_source_document(make_document_id(work_id, version))) is not None:
        latest = document
        version += 1
    return latest


def _section_count(store: Store, document_id: str) -> int:
    count = 0
    while store.get_section(make_section_id(document_id, count)) is not None:
        count += 1
    return count
