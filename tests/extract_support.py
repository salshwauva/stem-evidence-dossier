"""Shared setup for the extraction tests: one invented paper with two sections in a store."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from evidence_dossier.extract import ProviderResponse, RecordedProvider, build_prompt, prompt_key
from evidence_dossier.model import (
    Domain,
    ResearchWork,
    Section,
    SectionType,
    SourceDocument,
    SourceLevel,
    make_document_id,
    make_section_id,
    make_work_id,
)
from evidence_dossier.profiles import get_profile
from evidence_dossier.store import Store

FIXTURES = Path(__file__).parent / "fixtures" / "extract"
NOW = datetime(2026, 9, 12, 7, 0, tzinfo=UTC)
MODEL = "recorded-model-a"

RESULTS_TEXT = (
    "On Benchmark X, ResNet50 reached 76.1 percent top-1 accuracy, while the VGG-16 "
    "baseline reached 71.3 percent. On an A100 GPU the same ResNet50 model ran at 2100 "
    "images per second, against 1400 images per second on a V100."
)
DISCUSSION_TEXT = (
    "Label smoothing raised top-1 accuracy by 0.8 points on Benchmark X compared with "
    "the run without label smoothing."
)


@dataclass(frozen=True)
class Corpus:
    """A store with one computer science paper, plus the prompt that its extraction sends."""

    store: Store
    work: ResearchWork
    document: SourceDocument
    sections: tuple[Section, ...]
    prompt: str

    def provider(self, text: str) -> RecordedProvider:
        """Return a provider that answers the prompt of this paper with the given text."""
        response = ProviderResponse(model_identifier=MODEL, text=text)
        return RecordedProvider({prompt_key(self.prompt): response})


def add_paper(
    store: Store,
    arxiv_id: str,
    texts: tuple[str, ...],
    domain: Domain = Domain.COMPUTER_SCIENCE,
) -> Corpus:
    """Add a work, a document and one section per text, then return them with their prompt."""
    work = ResearchWork(
        id=make_work_id("arxiv", arxiv_id),
        title="Test paper on image classification throughput",
        domain=domain,
        external_identifiers={"arxiv": arxiv_id},
    )
    raw_text = "\n\n".join(texts)
    document = SourceDocument(
        id=make_document_id(work.id, version=1),
        research_work_id=work.id,
        version=1,
        source_level=SourceLevel.FULL_TEXT,
        source_format="text",
        raw_text=raw_text,
        content_sha256=hashlib.sha256(raw_text.encode()).hexdigest(),
        fetched_at=NOW,
    )
    types = (SectionType.RESULTS, SectionType.DISCUSSION, SectionType.OTHER)
    sections = tuple(
        Section(
            id=make_section_id(document.id, ordinal=n),
            document_id=document.id,
            ordinal=n,
            section_type=types[min(n, len(types) - 1)],
            text=text,
        )
        for n, text in enumerate(texts)
    )
    store.add_work(work)
    store.add_source_document(document)
    for section in sections:
        store.add_section(section)
    prompt = build_prompt(document, sections, get_profile(domain))
    return Corpus(store, work, document, sections, prompt)


def paper_corpus(store: Store) -> Corpus:
    return add_paper(store, "2409.00001", (RESULTS_TEXT, DISCUSSION_TEXT))


def valid_response() -> str:
    return (FIXTURES / "valid_two_studies.json").read_text(encoding="utf-8")
