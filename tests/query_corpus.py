"""Invented claims for the query tests, on top of the two factory papers.

Every work, passage and value here is made up for the tests.
"""

from collections.abc import Sequence
from dataclasses import replace
from datetime import date

from evidence_dossier.model import (
    ClaimType,
    Comparator,
    Domain,
    EvidenceClaim,
    Measurement,
    ResearchContext,
    ResearchWork,
    Result,
    ResultDirection,
    Section,
    SectionType,
    SourceLevel,
    Study,
    Term,
    make_section_id,
    make_work_id,
)
from evidence_dossier.store import Store
from tests.factories import (
    Paper,
    _document,
    _span,
    _valid_run,
    biology_paper,
    computer_science_paper,
)


def _paper(
    key: str,
    *,
    domain: Domain,
    text: str,
    passage: str,
    subject: str,
    outcome: str,
    measurement: str,
    comparator: str | None,
    direction: ResultDirection,
    significance: bool | None = True,
) -> Paper:
    work_id = make_work_id("test", key)
    work = ResearchWork(
        id=work_id, title=f"Test work {key}", domain=domain, publication_date=date(2025, 1, 1)
    )
    document = _document(work_id, text, SourceLevel.FULL_TEXT)
    section = Section(
        id=make_section_id(document.id, ordinal=0),
        document_id=document.id,
        ordinal=0,
        section_type=SectionType.RESULTS,
        text=text,
    )
    study = Study(id=f"study-{key}", research_work_id=work_id, description=f"Study {key}")
    claim = EvidenceClaim(
        id=f"claim-{key}",
        research_work_id=work_id,
        study_id=study.id,
        claim_type=ClaimType.EFFECT,
        claim_text=passage,
        subject=Term(original=subject),
        predicate=direction.value.lower(),
        outcome=outcome,
        research_context=ResearchContext(domain=domain),
        comparator=None if comparator is None else Comparator(name=Term(original=comparator)),
        measurement=Measurement(name=Term(original=measurement)),
        result=Result(direction=direction, statistical_significance=significance),
        evidence_span=_span(work_id, section, passage),
    )
    return Paper(work, document, section, study, _valid_run(key, document.id), claim)


def retrieval_papers() -> list[Paper]:
    """The two factory papers plus four invented claims in other topics."""
    return [
        biology_paper(),
        computer_science_paper(),
        _paper(
            "caching",
            domain=Domain.COMPUTER_SCIENCE,
            text="Prompt caching cut median latency by 41% against uncached requests.",
            passage="Prompt caching cut median latency by 41%",
            subject="prompt caching",
            outcome="latency",
            measurement="median latency",
            comparator="uncached requests",
            direction=ResultDirection.DECREASED,
        ),
        _paper(
            "catalyst",
            domain=Domain.CHEMISTRY,
            text="The palladium catalyst raised the coupling yield to 88% from 61% without it.",
            passage="The palladium catalyst raised the coupling yield to 88%",
            subject="palladium catalyst",
            outcome="coupling yield",
            measurement="isolated yield",
            comparator="no catalyst",
            direction=ResultDirection.INCREASED,
        ),
        _paper(
            "graphene",
            domain=Domain.PHYSICS,
            text="Graphene doping lowered the sheet resistance relative to pristine films.",
            passage="Graphene doping lowered the sheet resistance",
            subject="graphene doping",
            outcome="sheet resistance",
            measurement="sheet resistance",
            comparator="pristine films",
            direction=ResultDirection.DECREASED,
        ),
        _paper(
            "sirt1",
            domain=Domain.BIOLOGY,
            text="SIRT1 overexpression did not change mitochondrial density in muscle fibres.",
            passage="SIRT1 overexpression did not change mitochondrial density",
            subject="SIRT1 overexpression",
            outcome="mitochondrial density",
            measurement="mitochondrial density",
            comparator="wild type fibres",
            direction=ResultDirection.UNCHANGED,
            significance=False,
        ),
    ]


STANCE_TEXT = (
    "With retrieval the hallucination rate fell against the same model without retrieval. "
    "With retrieval the hallucination rate rose against the same model without retrieval. "
    "Retrieval cut hallucination on open questions but raised it on closed questions. "
    "Retrieval left the hallucination rate unchanged against the same model without retrieval. "
    "Retrieval raised answer quality against the same model without retrieval. "
    "Prompt caching cut latency against uncached requests."
)

# One invented claim per stance value, for the RAG proposition from plan section 58.
_STANCE_SPECS: tuple[tuple[str, str, str, str, str, str, ResultDirection, bool | None], ...] = (
    (
        "supports",
        "the hallucination rate fell",
        "retrieval-augmented generation",
        "factual hallucination",
        "hallucination rate",
        "same model without retrieval",
        ResultDirection.DECREASED,
        True,
    ),
    (
        "contradicts",
        "the hallucination rate rose",
        "retrieval-augmented generation",
        "factual hallucination",
        "hallucination rate",
        "same model without retrieval",
        ResultDirection.INCREASED,
        True,
    ),
    (
        "mixed",
        "cut hallucination on open questions but raised it on closed questions",
        "retrieval-augmented generation",
        "factual hallucination",
        "hallucination rate",
        "same model without retrieval",
        ResultDirection.MIXED,
        None,
    ),
    (
        "null",
        "left the hallucination rate unchanged",
        "retrieval-augmented generation",
        "factual hallucination",
        "hallucination rate",
        "same model without retrieval",
        ResultDirection.UNCHANGED,
        False,
    ),
    (
        "indirect",
        "raised answer quality",
        "retrieval-augmented generation",
        "factual hallucination",
        "answer quality",
        "same model without retrieval",
        ResultDirection.IMPROVED,
        True,
    ),
    (
        "incomparable",
        "Prompt caching cut latency",
        "prompt caching",
        "latency",
        "median latency",
        "uncached requests",
        ResultDirection.DECREASED,
        True,
    ),
)


def stance_paper() -> tuple[Paper, list[EvidenceClaim]]:
    """One work whose six claims exercise every branch of the stance classifier.

    The paper carries the first claim. The other five come back as extra claims.
    """
    base = _paper(
        "stance",
        domain=Domain.COMPUTER_SCIENCE,
        text=STANCE_TEXT,
        passage="the hallucination rate fell",
        subject="retrieval-augmented generation",
        outcome="factual hallucination",
        measurement="hallucination rate",
        comparator="same model without retrieval",
        direction=ResultDirection.DECREASED,
    )
    claims = [
        base.claim.model_copy(
            update={
                "id": f"claim-{key}",
                "claim_text": passage,
                "subject": Term(original=subject),
                "outcome": outcome,
                "measurement": Measurement(name=Term(original=measurement)),
                "comparator": Comparator(name=Term(original=comparator)),
                "result": Result(direction=direction, statistical_significance=significance),
                "evidence_span": _span(base.work.id, base.section, passage),
            }
        )
        for key, passage, subject, outcome, measurement, comparator, direction, significance in _STANCE_SPECS
    ]
    return replace(base, claim=claims[0]), claims[1:]


def seed(store: Store, papers: list[Paper], extra_claims: Sequence[EvidenceClaim] = ()) -> None:
    for paper in papers:
        store.add_work(paper.work)
        store.add_source_document(paper.document)
        store.add_section(paper.section)
        store.add_study(paper.study)
        store.add_extraction_run(paper.run)
        store.add_claim(paper.claim)
    for claim in extra_claims:
        store.add_claim(claim)
