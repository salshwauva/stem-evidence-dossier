from typing import Any

from evidence_dossier.model import (
    BiologyAttributes,
    ComputerScienceAttributes,
    Domain,
    EvidenceClaim,
    ResultDirection,
)

# Payloads shaped like extractor output. The sentences are invented for the tests.
BIOLOGY_CLAIM: dict[str, Any] = {
    "id": "claim-bio-1",
    "research_work_id": "work-bio",
    "study_id": "study-bio-1",
    "claim_type": "EFFECT",
    "claim_text": "MAPT knockdown increased neuronal survival compared with a scrambled control.",
    "subject": {"original": "tau knockdown", "canonical": "MAPT knockdown"},
    "predicate": "increased",
    "outcome": "neuronal survival",
    "research_context": {
        "domain": "BIOLOGY",
        "system": "cortical neurons",
        "domain_attributes": {
            "profile": "biology",
            "organism": "Homo sapiens",
            "cell_line": "iPSC-derived cortical neurons",
            "disease_model": "MAPT P301L frontotemporal dementia model",
            "intervention": "antisense oligonucleotide",
            "dose": "5 uM",
            "duration": "14 days",
            "assay": "live-cell imaging",
        },
    },
    "method": {"name": {"original": "ASO knockdown", "canonical": "antisense knockdown"}},
    "comparator": {"name": {"original": "scrambled ASO"}},
    "measurement": {"name": {"original": "neuronal survival"}, "unit": {"original": "%"}},
    "result": {"direction": "INCREASED", "value": 32.0, "unit": {"original": "%"}},
    "evidence_span": {
        "research_work_id": "work-bio",
        "section_id": "section-bio-results",
        "start_offset": 0,
        "end_offset": 32,
        "source_text": "Knockdown raised survival by 32%",
    },
}

COMPUTER_SCIENCE_CLAIM: dict[str, Any] = {
    "id": "claim-cs-1",
    "research_work_id": "work-cs",
    "study_id": "study-cs-1",
    "claim_type": "PERFORMANCE",
    "claim_text": "Retrieval lowered the factual error rate against the same model without retrieval.",
    "subject": {"original": "RAG", "canonical": "retrieval-augmented generation"},
    "predicate": "reduces",
    "outcome": "factual error rate",
    "research_context": {
        "domain": "COMPUTER_SCIENCE",
        "dataset": "Benchmark X",
        "domain_attributes": {
            "profile": "computer_science",
            "task": "factual question answering",
            "model": "Llama-family model",
            "benchmark": "Benchmark X",
            "evaluation_metric": "factual error rate",
        },
    },
    "method": {
        "name": {"original": "RAG", "canonical": "retrieval-augmented generation"},
        "domain_attributes": {"profile": "computer_science", "algorithm": "dense retrieval"},
    },
    "comparator": {
        "name": {"original": "no retrieval", "canonical": "same model without retrieval"}
    },
    "measurement": {"name": {"original": "factual error rate"}, "unit": {"original": "%"}},
    "result": {"direction": "DECREASED", "value": 11.5, "unit": {"original": "%"}},
    "evidence_span": {
        "research_work_id": "work-cs",
        "section_id": "section-cs-results",
        "start_offset": 0,
        "end_offset": 26,
        "source_text": "Retrieval cut errors to 11",
    },
}


def test_biology_and_computer_science_claims_share_one_claim_model() -> None:
    biology = EvidenceClaim.model_validate(BIOLOGY_CLAIM)
    computer_science = EvidenceClaim.model_validate(COMPUTER_SCIENCE_CLAIM)

    assert biology.research_context.domain is Domain.BIOLOGY
    bio_attributes = biology.research_context.domain_attributes
    assert isinstance(bio_attributes, BiologyAttributes)
    assert bio_attributes.organism == "Homo sapiens"
    assert bio_attributes.assay == "live-cell imaging"
    assert biology.result.direction is ResultDirection.INCREASED

    assert computer_science.research_context.domain is Domain.COMPUTER_SCIENCE
    cs_attributes = computer_science.research_context.domain_attributes
    assert isinstance(cs_attributes, ComputerScienceAttributes)
    assert cs_attributes.benchmark == "Benchmark X"
    assert computer_science.method is not None
    method_attributes = computer_science.method.domain_attributes
    assert isinstance(method_attributes, ComputerScienceAttributes)
    assert method_attributes.algorithm == "dense retrieval"
    assert computer_science.result.direction is ResultDirection.DECREASED


def test_claim_names_keep_original_text_next_to_canonical_value() -> None:
    claim = EvidenceClaim.model_validate(COMPUTER_SCIENCE_CLAIM)

    assert claim.subject.original == "RAG"
    assert claim.subject.canonical == "retrieval-augmented generation"
    assert claim.measurement is not None
    assert claim.measurement.name.original == "factual error rate"
    assert claim.measurement.name.canonical is None
