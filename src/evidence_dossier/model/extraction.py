"""Extraction audit records (plan sections 31 and 46)."""

from datetime import datetime

from evidence_dossier.model.base import FrozenModel
from evidence_dossier.model.enums import ValidationStatus


class ExtractionRun(FrozenModel):
    """One extractor call on one source document.

    The raw response and the errors stay stored when validation fails, so
    invalid output stays available for analysis.
    """

    id: str
    source_document_id: str
    model_identifier: str
    prompt_version: str
    schema_version: str
    created_at: datetime
    raw_response: str
    validation_status: ValidationStatus
    errors: tuple[str, ...] = ()
