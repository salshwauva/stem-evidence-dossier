"""The domain-independent core model.

This package imports nothing from the other evidence_dossier subpackages.
"""

from evidence_dossier.model.attributes import (
    BiologyAttributes,
    ComputerScienceAttributes,
    DomainAttributes,
)
from evidence_dossier.model.base import FrozenModel
from evidence_dossier.model.claim import (
    Comparator,
    EvidenceClaim,
    EvidenceSpan,
    Measurement,
    Method,
    ResearchContext,
    Result,
    Study,
    Term,
)
from evidence_dossier.model.document import Section, SourceDocument
from evidence_dossier.model.enums import (
    ClaimType,
    ComparabilityLevel,
    Domain,
    ResultDirection,
    SectionType,
    SourceLevel,
    Stance,
    ValidationStatus,
    WorkLinkRelation,
)
from evidence_dossier.model.extraction import ExtractionRun
from evidence_dossier.model.ids import make_document_id, make_section_id, make_work_id
from evidence_dossier.model.work import Author, ResearchWork, WorkLink

__all__ = [
    "Author",
    "BiologyAttributes",
    "ClaimType",
    "ComparabilityLevel",
    "Comparator",
    "ComputerScienceAttributes",
    "Domain",
    "DomainAttributes",
    "EvidenceClaim",
    "EvidenceSpan",
    "ExtractionRun",
    "FrozenModel",
    "Measurement",
    "Method",
    "ResearchContext",
    "ResearchWork",
    "Result",
    "ResultDirection",
    "Section",
    "SectionType",
    "SourceDocument",
    "SourceLevel",
    "Stance",
    "Study",
    "Term",
    "ValidationStatus",
    "WorkLink",
    "WorkLinkRelation",
    "make_document_id",
    "make_section_id",
    "make_work_id",
]
