"""The extraction pipeline for one source document (plan sections 31, 46 and 47).

extract_document builds the prompt, calls the provider, validates the reply,
normalizes the claims and stores the run. An invalid reply is stored as an
INVALID run with its raw response and its errors, and no claim is stored
(plan section 31). The pipeline takes the normalizer as an argument, typed by
the Normalizer protocol, so extract never imports normalize. Methodological
reporting flags (plan section 44) are out of scope for this increment.
"""

import hashlib
from datetime import datetime
from typing import Protocol

from evidence_dossier.extract.candidates import CandidateClaim
from evidence_dossier.extract.prompt import PROMPT_VERSION, build_prompt
from evidence_dossier.extract.providers import ExtractionProvider
from evidence_dossier.extract.validation import slug, validate_response
from evidence_dossier.model import (
    Comparator,
    EvidenceClaim,
    EvidenceSpan,
    ExtractionRun,
    Measurement,
    Method,
    ResearchContext,
    ResearchWork,
    Result,
    Study,
    Term,
    ValidationStatus,
)
from evidence_dossier.profiles import DomainProfile, get_profile
from evidence_dossier.store import Store


class Normalizer(Protocol):
    """Fills the canonical values of a claim. normalize.normalize_claim has this shape."""

    def __call__(self, claim: EvidenceClaim, profile: DomainProfile) -> EvidenceClaim: ...


def extract_document(
    store: Store,
    document_id: str,
    provider: ExtractionProvider,
    *,
    normalizer: Normalizer,
    schema_version: str = "core-1",
    now: datetime,
) -> ExtractionRun:
    """Extract the claims of one stored document and return the stored run.

    Claim IDs are "<document_id>_c<n>" in reply order, and study IDs are
    "<document_id>_<study key slug>". The run ID hashes the prompt and the
    reply, so the same reply to the same prompt gives the same run ID.
    """
    document = store.get_source_document(document_id)
    if document is None:
        raise LookupError(f"document {document_id} is not in the store")
    work = store.get_work(document.research_work_id)
    if work is None:
        raise LookupError(f"work {document.research_work_id} is not in the store")
    sections = tuple(store.list_sections(document_id))
    profile = get_profile(work.domain)
    prompt = build_prompt(document, sections, profile)
    response = provider.complete(prompt)
    outcome = validate_response(response.text, document, sections)
    run = ExtractionRun(
        id=f"{document_id}_run_{hashlib.sha256((prompt + response.text).encode()).hexdigest()[:12]}",
        source_document_id=document_id,
        model_identifier=response.model_identifier,
        prompt_version=PROMPT_VERSION,
        schema_version=schema_version,
        created_at=now,
        raw_response=response.text,
        validation_status=ValidationStatus.INVALID if outcome.errors else ValidationStatus.VALID,
        errors=outcome.errors,
    )
    if outcome.candidates is None:
        store.add_extraction_run(run)
        return run
    studies = [
        Study(
            id=f"{document_id}_{slug(study.key)}",
            research_work_id=work.id,
            description=study.description,
        )
        for study in outcome.candidates.studies
    ]
    claims = [
        normalizer(
            _build_claim(candidate, span, work, f"{document_id}_c{n}", run.id, document_id),
            profile,
        )
        for n, (candidate, span) in enumerate(
            zip(outcome.candidates.claims, outcome.spans, strict=True), start=1
        )
    ]
    store.add_extraction_run(run)
    for study in studies:
        store.add_study(study)
    for claim in claims:
        store.add_claim(claim)
    return run


def _build_claim(
    candidate: CandidateClaim,
    span: EvidenceSpan,
    work: ResearchWork,
    claim_id: str,
    run_id: str,
    document_id: str,
) -> EvidenceClaim:
    """Turn a validated candidate into a core claim. Every Term keeps its original text."""
    method = candidate.method
    comparator = candidate.comparator
    measurement = candidate.measurement
    result = candidate.result
    return EvidenceClaim(
        id=claim_id,
        research_work_id=work.id,
        study_id=f"{document_id}_{slug(candidate.study_key)}",
        extraction_run_id=run_id,
        claim_type=candidate.claim_type,
        claim_text=candidate.claim_text,
        subject=Term(original=candidate.subject),
        predicate=candidate.predicate,
        outcome=candidate.outcome,
        research_context=ResearchContext(
            domain=work.domain, **candidate.research_context.model_dump()
        ),
        method=None
        if method is None
        else Method(
            name=Term(original=method.name),
            method_type=method.method_type,
            parameters=method.parameters,
            domain_attributes=method.domain_attributes,
        ),
        comparator=None
        if comparator is None
        else Comparator(
            name=Term(original=comparator.name),
            comparator_type=comparator.comparator_type,
            configuration=comparator.configuration,
            domain_attributes=comparator.domain_attributes,
        ),
        measurement=None
        if measurement is None
        else Measurement(
            name=Term(original=measurement.name),
            category=measurement.category,
            measurement_method=measurement.measurement_method,
            unit=None if measurement.unit is None else Term(original=measurement.unit),
        ),
        result=Result(
            direction=result.direction,
            value=result.value,
            unit=None if result.unit is None else Term(original=result.unit),
            effect_size=result.effect_size,
            uncertainty=result.uncertainty,
            statistical_significance=result.statistical_significance,
            p_value=result.p_value,
            confidence_interval=result.confidence_interval,
            result_text=result.result_text,
        ),
        evidence_span=span,
    )
