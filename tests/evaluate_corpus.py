"""A store seeded from the gold fixture, for the tests of evaluate.run.

The gold files hold the claims and their offsets. Everything the store needs
around them is invented here: the work titles, the section text between the
evidence spans, and the study descriptions. The stored IDs follow no gold key
convention, so a test proves that the run maps a stored claim onto its gold
key through the evidence span.
"""

import hashlib
from datetime import date
from typing import Any

from evidence_dossier.evaluate import Dataset, GoldClaim, GoldDocument, load_dataset
from evidence_dossier.model import (
    EvidenceClaim,
    ResearchWork,
    Section,
    SectionType,
    SourceDocument,
    Study,
)
from evidence_dossier.store import Store
from tests.evaluate_predictions import FIXTURE_DIR
from tests.factories import FETCHED_AT, _valid_run

FILLER = "."


def dev_dataset() -> Dataset:
    return load_dataset(FIXTURE_DIR, "dev")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:8]


def stored_claim_id(claim: GoldClaim) -> str:
    """The ID the store holds for one gold claim. It shares no text with the gold key."""
    return f"stored-claim-{_digest(claim.claim_key)}"


def study_id(study_key: str) -> str:
    """The stored study ID of one gold study key. The run finds it through the spans."""
    return f"stored-study-{_digest(study_key)}"


def _section_text(spans: list[tuple[int, int, str]]) -> str:
    """Build section text that holds every span at its offsets. The gaps hold filler."""
    end = max(stop for _, stop, _ in spans)
    text = [FILLER] * end
    for start, stop, source_text in spans:
        text[start:stop] = list(source_text)
    return "".join(text)


def sections_of(document: GoldDocument) -> list[Section]:
    spans: dict[str, list[tuple[int, int, str]]] = {}
    for claim in document.claims:
        span = claim.evidence_span
        spans.setdefault(span.section_id, []).append(
            (span.start_offset, span.end_offset, span.source_text)
        )
    return [
        Section(
            id=section_id,
            document_id=document.document_id,
            ordinal=int(section_id.rsplit("_s", 1)[1]),
            section_type=SectionType.RESULTS,
            text=_section_text(parts),
        )
        for section_id, parts in sorted(spans.items())
    ]


def claim_of(gold: GoldClaim, run_id: str) -> EvidenceClaim:
    """Turn a gold claim into the claim the extractor stored, with no other change."""
    values: dict[str, Any] = gold.model_dump(exclude={"gold_key", "study_key"})
    values.update(
        id=stored_claim_id(gold), study_id=study_id(gold.study_key), extraction_run_id=run_id
    )
    return EvidenceClaim.model_validate(values)


def seed(store: Store, dataset: Dataset) -> None:
    """Write every work, document, section, study, run and claim of the dataset."""
    for document in dataset.documents:
        sections = sections_of(document)
        raw_text = "\n".join(section.text for section in sections)
        work_id = document.research_work_id
        store.add_work(
            ResearchWork(
                id=work_id,
                title=f"Invented work {work_id}",
                domain=document.claims[0].research_context.domain,
                publication_date=date(2025, 1, 1),
            )
        )
        store.add_source_document(
            SourceDocument(
                id=document.document_id,
                research_work_id=work_id,
                version=int(document.document_id.rsplit("_v", 1)[1]),
                source_level=document.source_level,
                source_format="invented",
                raw_text=raw_text,
                content_sha256=hashlib.sha256(raw_text.encode()).hexdigest(),
                fetched_at=FETCHED_AT,
            )
        )
        for section in sections:
            store.add_section(section)
        run = _valid_run(work_id, document.document_id)
        store.add_extraction_run(run)
        for study_key in dict.fromkeys(claim.study_key for claim in document.claims):
            store.add_study(
                Study(
                    id=study_id(study_key),
                    research_work_id=work_id,
                    description=f"Invented study {study_key}",
                )
            )
        for gold in document.claims:
            store.add_claim(claim_of(gold, run.id))
