"""Record builders for the store tests. The works, passages and values are invented."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime

from evidence_dossier.model import (
    Author,
    BiologyAttributes,
    ClaimType,
    Comparator,
    ComputerScienceAttributes,
    Domain,
    EvidenceClaim,
    EvidenceSpan,
    ExtractionRun,
    Measurement,
    Method,
    ResearchContext,
    ResearchWork,
    Result,
    ResultDirection,
    Section,
    SectionType,
    SourceDocument,
    SourceLevel,
    Study,
    Term,
    ValidationStatus,
    make_document_id,
    make_section_id,
    make_work_id,
)

FETCHED_AT = datetime(2026, 9, 11, 8, 30, tzinfo=UTC)

# Truncated JSON with an unknown claim type, quotes, backslashes, non-ASCII text and a newline.
INVALID_RAW_RESPONSE = (
    '{"claims": [{"subject": "RAG", "claim_type": "PERFORMANCE_GAIN",\n'
    '  "claim_text": "dose \u2265 5 \u00b5M", "path": "C:\\\\runs\\\\a"'
)
INVALID_ERRORS = (
    "claims.0.claim_type: input is not a known claim type",
    "response ended before the JSON object closed",
)


@dataclass(frozen=True)
class Paper:
    """One work with a source document, a section, a study, an extraction run and a claim."""

    work: ResearchWork
    document: SourceDocument
    section: Section
    study: Study
    run: ExtractionRun
    claim: EvidenceClaim


def _document(work_id: str, text: str, source_level: SourceLevel) -> SourceDocument:
    return SourceDocument(
        id=make_document_id(work_id, version=1),
        research_work_id=work_id,
        version=1,
        source_level=source_level,
        source_format="jats_xml",
        raw_text=text,
        content_sha256=hashlib.sha256(text.encode()).hexdigest(),
        fetched_at=FETCHED_AT,
    )


def _span(work_id: str, section: Section, passage: str) -> EvidenceSpan:
    start = section.text.index(passage)
    return EvidenceSpan(
        research_work_id=work_id,
        section_id=section.id,
        start_offset=start,
        end_offset=start + len(passage),
        source_text=passage,
    )


def _valid_run(key: str, document_id: str) -> ExtractionRun:
    return ExtractionRun(
        id=f"run-{key}",
        source_document_id=document_id,
        model_identifier="extractor-model-a",
        prompt_version="claims-v1",
        schema_version="core-1",
        created_at=FETCHED_AT,
        raw_response='{"claims": ["one claim"]}',
        validation_status=ValidationStatus.VALID,
    )


def invalid_run(document_id: str) -> ExtractionRun:
    return ExtractionRun(
        id="run-invalid",
        source_document_id=document_id,
        model_identifier="extractor-model-a",
        prompt_version="claims-v1",
        schema_version="core-1",
        created_at=FETCHED_AT,
        raw_response=INVALID_RAW_RESPONSE,
        validation_status=ValidationStatus.INVALID,
        errors=INVALID_ERRORS,
    )


def biology_paper(pmid: str = "12345678") -> Paper:
    work_id = make_work_id("pmid", pmid)
    work = ResearchWork(
        id=work_id,
        title="MAPT knockdown and neuronal survival in a test dementia model",
        domain=Domain.BIOLOGY,
        doi=f"10.5555/bio.{pmid}",
        abstract="Knockdown of MAPT raised neuronal survival.",
        publication_date=date(2025, 3, 14),
        venue="Journal of Test Neuroscience",
        authors=(
            Author(name="A. Rivera", affiliations=("Neurodegeneration Lab, Test University",)),
            Author(
                name="B. Okafor",
                affiliations=("Neurodegeneration Lab, Test University", "Test Institute"),
            ),
        ),
        external_identifiers={"pmid": pmid},
    )
    text = (
        "Knockdown of MAPT raised neuronal survival by 32% relative to a scrambled control "
        "(p < 0.01)."
    )
    document = _document(work_id, text, SourceLevel.ABSTRACT_ONLY)
    section = Section(
        id=make_section_id(document.id, ordinal=0),
        document_id=document.id,
        ordinal=0,
        section_type=SectionType.ABSTRACT,
        text=text,
    )
    study = Study(
        id=f"study-{pmid}",
        research_work_id=work_id,
        description="Antisense knockdown of MAPT in iPSC-derived cortical neurons",
    )
    run = _valid_run(pmid, document.id)
    claim = EvidenceClaim(
        id=f"claim-{pmid}",
        research_work_id=work_id,
        study_id=study.id,
        extraction_run_id=run.id,
        claim_type=ClaimType.EFFECT,
        claim_text="MAPT knockdown increased neuronal survival compared with a scrambled control.",
        subject=Term(original="knockdown of MAPT", canonical="MAPT knockdown"),
        predicate="increased",
        outcome="neuronal survival",
        research_context=ResearchContext(
            domain=Domain.BIOLOGY,
            system="cortical neurons",
            domain_attributes=BiologyAttributes(
                organism="Homo sapiens",
                cell_line="iPSC-derived cortical neurons",
                intervention="antisense oligonucleotide",
                dose="5 uM",
                duration="14 days",
                assay="live-cell imaging",
            ),
        ),
        method=Method(
            name=Term(original="ASO knockdown", canonical="antisense knockdown"),
            method_type="knockdown",
            parameters={"dose": "5 uM"},
            domain_attributes=BiologyAttributes(intervention="antisense oligonucleotide"),
        ),
        comparator=Comparator(
            name=Term(original="scrambled control", canonical="scrambled ASO"),
            comparator_type="control group",
        ),
        measurement=Measurement(
            name=Term(original="neuronal survival", canonical="neuronal survival"),
            category="cell viability",
            unit=Term(original="%"),
        ),
        result=Result(
            direction=ResultDirection.INCREASED,
            value=32.0,
            unit=Term(original="%"),
            statistical_significance=True,
            p_value="< 0.01",
            result_text="raised neuronal survival by 32%",
        ),
        evidence_span=_span(work_id, section, "raised neuronal survival by 32%"),
    )
    return Paper(work, document, section, study, run, claim)


def computer_science_paper(arxiv_id: str = "2401.01234") -> Paper:
    work_id = make_work_id("arxiv", arxiv_id)
    work = ResearchWork(
        id=work_id,
        title="Retrieval and factual errors in a test language model",
        domain=Domain.COMPUTER_SCIENCE,
        publication_date=date(2024, 1, 5),
        venue="arXiv",
        authors=(Author(name="C. Lindqvist", affiliations=("Test Systems Group",)),),
        external_identifiers={"arxiv": arxiv_id},
    )
    text = "With retrieval, the factual error rate fell from 18.2% to 11.5% on Benchmark X."
    document = _document(work_id, text, SourceLevel.FULL_TEXT)
    section = Section(
        id=make_section_id(document.id, ordinal=4),
        document_id=document.id,
        ordinal=4,
        section_type=SectionType.RESULTS,
        heading="Results",
        text=text,
    )
    study = Study(
        id=f"study-{arxiv_id}",
        research_work_id=work_id,
        description="Retrieval against the same model without retrieval on Benchmark X",
    )
    run = _valid_run(arxiv_id, document.id)
    claim = EvidenceClaim(
        id=f"claim-{arxiv_id}",
        research_work_id=work_id,
        study_id=study.id,
        extraction_run_id=run.id,
        claim_type=ClaimType.PERFORMANCE,
        claim_text="Retrieval lowered the factual error rate against the same model without it.",
        normalized_claim="retrieval-augmented generation reduces factual error rate",
        subject=Term(original="retrieval", canonical="retrieval-augmented generation"),
        predicate="reduces",
        outcome="factual error rate",
        research_context=ResearchContext(
            domain=Domain.COMPUTER_SCIENCE,
            dataset="Benchmark X",
            model="test language model",
            theoretical_assumptions=("closed-book baseline",),
            domain_attributes=ComputerScienceAttributes(
                task="factual question answering",
                model_version="v2",
                benchmark="Benchmark X",
                evaluation_metric="factual error rate",
            ),
        ),
        method=Method(
            name=Term(original="retrieval", canonical="retrieval-augmented generation"),
            parameters={"top_k": "5"},
            domain_attributes=ComputerScienceAttributes(algorithm="dense retrieval"),
        ),
        comparator=Comparator(
            name=Term(original="no retrieval", canonical="same model without retrieval"),
            configuration="closed book",
            domain_attributes=ComputerScienceAttributes(baseline="closed-book prompting"),
        ),
        measurement=Measurement(
            name=Term(original="factual error rate", canonical="factual error rate"),
            measurement_method="human review",
            unit=Term(original="%", canonical="percent"),
        ),
        result=Result(
            direction=ResultDirection.DECREASED,
            value=11.5,
            unit=Term(original="%", canonical="percent"),
            effect_size=-6.7,
            uncertainty="standard deviation over three seeds",
            confidence_interval="10.9 to 12.1",
            result_text="the factual error rate fell from 18.2% to 11.5%",
        ),
        evidence_span=_span(work_id, section, "the factual error rate fell from 18.2% to 11.5%"),
    )
    return Paper(work, document, section, study, run, claim)
