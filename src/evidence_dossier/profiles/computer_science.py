"""The computer science profile."""

from dataclasses import dataclass

from evidence_dossier.model import ComputerScienceAttributes, Domain
from evidence_dossier.profiles.base import (
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)


@dataclass(frozen=True)
class ComputerScienceProfile(DomainProfile):
    """Computer science profile. The values come from plan sections 18, 20, 25, 38 and 43."""

    domain: Domain = Domain.COMPUTER_SCIENCE
    attribute_model: AttributeModel | None = ComputerScienceAttributes
    expected_entities: tuple[str, ...] = (
        "task",
        "algorithm",
        "model",
        "model version",
        "dataset",
        "benchmark",
        "training data",
        "hardware",
        "baseline",
        "hyperparameters",
        "evaluation metric",
        "compute budget",
    )
    common_methods: tuple[str, ...] = (
        "algorithm",
        "architecture",
        "training procedure",
        "retrieval system",
        "compiler optimization",
        "networking strategy",
    )
    common_measurement_types: tuple[str, ...] = (
        "accuracy",
        "F1",
        "latency",
        "throughput",
        "energy consumption",
    )
    evidence_gap_dimensions: tuple[str, ...] = (
        *GENERIC_EVIDENCE_GAP_DIMENSIONS,
        "unseen datasets",
        "different model families",
        "hardware variation",
        "deployment evidence",
        "longitudinal evaluation",
    )
    comparability_features: tuple[str, ...] = (
        "task",
        "dataset",
        "model family",
        "baseline",
        "metric",
        "hardware",
        "evaluation conditions",
    )
