"""Deterministic IDs for research works, source documents and sections.

A second ingestion of the same source yields the same IDs. The work ID is a
hash, so identifiers that contain a slash (DOIs, old arXiv IDs) stay safe in
URL paths.
"""

import hashlib


def make_work_id(scheme: str, value: str) -> str:
    """Return the ID of the work with this source identifier, such as ("pmid", "90000001").

    The function does no normalization, so the ingest code passes the
    identifier exactly as the source returns it.
    """
    digest = hashlib.sha256(f"{scheme}:{value}".encode()).hexdigest()
    return f"work_{digest[:16]}"


def make_document_id(work_id: str, version: int) -> str:
    """Return the ID of one version of the text of a work. A change to the text is a new version."""
    return f"{work_id}_v{version}"


def make_section_id(document_id: str, ordinal: int) -> str:
    """Return the ID of the section at this position in a document."""
    return f"{document_id}_s{ordinal}"
