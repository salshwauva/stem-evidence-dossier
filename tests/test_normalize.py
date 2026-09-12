import pytest

from evidence_dossier.model import (
    ClaimType,
    Comparator,
    Domain,
    EvidenceClaim,
    Measurement,
    Method,
    ResearchContext,
    Result,
    ResultDirection,
    Term,
)
from evidence_dossier.normalize import (
    NAME_SYNONYMS,
    UNIT_SYNONYMS,
    canonical_name,
    canonical_unit,
    fold_key,
    fold_name,
    normalize_claim,
)
from evidence_dossier.profiles import get_profile
from tests.factories import computer_science_paper


@pytest.mark.parametrize(
    ("domain", "original", "canonical"),
    [
        (Domain.COMPUTER_SCIENCE, "ResNet-50", "ResNet-50"),
        (Domain.COMPUTER_SCIENCE, "ResNet50", "ResNet-50"),
        (Domain.COMPUTER_SCIENCE, "ResNet 50", "ResNet-50"),
        (Domain.COMPUTER_SCIENCE, "resnet_50", "ResNet-50"),
        (Domain.COMPUTER_SCIENCE, "NVIDIA A100", "NVIDIA A100"),
        (Domain.COMPUTER_SCIENCE, "A100 GPU", "NVIDIA A100"),
        (Domain.COMPUTER_SCIENCE, "A100", "NVIDIA A100"),
        (Domain.BIOLOGY, "tau", "MAPT"),
        (Domain.BIOLOGY, "MAPT", "MAPT"),
        (Domain.BIOLOGY, "microtubule-associated protein tau", "MAPT"),
        (Domain.CHEMISTRY, "DCM", "dichloromethane"),
        (Domain.CHEMISTRY, "methylene chloride", "dichloromethane"),
        (Domain.CHEMISTRY, "THF", "tetrahydrofuran"),
    ],
)
def test_name_table_rows(domain: Domain, original: str, canonical: str) -> None:
    assert canonical_name(original, domain) == canonical


def test_name_tables_are_per_domain() -> None:
    assert canonical_name("tau", Domain.COMPUTER_SCIENCE) == "tau"
    assert canonical_name("A100", Domain.BIOLOGY) == "a100"


@pytest.mark.parametrize(
    ("original", "canonical"),
    [
        ("  Label   Smoothing ", "label smoothing"),
        ("top - 1 accuracy", "top-1 accuracy"),
        ("VGG-16 Baseline", "vgg-16 baseline"),
    ],
)
def test_unknown_names_fold_case_whitespace_and_hyphens(original: str, canonical: str) -> None:
    assert fold_name(original) == canonical
    assert canonical_name(original, Domain.PHYSICS) == canonical


@pytest.mark.parametrize(
    ("original", "canonical"),
    [
        ("seconds", "s"),
        ("sec", "s"),
        ("ms", "ms"),
        ("milliseconds", "ms"),
        ("%", "%"),
        ("percent", "%"),
        ("uM", "µM"),
        ("µM", "µM"),
        ("μM", "µM"),
        ("images/s", "images/s"),
        (" MB ", "MB"),
    ],
)
def test_unit_table_rows(original: str, canonical: str) -> None:
    assert canonical_unit(original) == canonical


def test_every_table_key_is_already_folded() -> None:
    for table in NAME_SYNONYMS.values():
        assert all(key == fold_key(key) for key in table)
    assert all(key == fold_key(key) for key in UNIT_SYNONYMS)


def _raw_claim() -> EvidenceClaim:
    """The factory claim with every canonical value removed."""
    claim = computer_science_paper().claim
    return EvidenceClaim(
        id=claim.id,
        research_work_id=claim.research_work_id,
        study_id=claim.study_id,
        claim_type=ClaimType.PERFORMANCE,
        claim_text=claim.claim_text,
        subject=Term(original="ResNet 50"),
        predicate="reaches",
        research_context=ResearchContext(domain=Domain.COMPUTER_SCIENCE),
        method=Method(name=Term(original="Label  Smoothing")),
        comparator=Comparator(name=Term(original="VGG-16 baseline")),
        measurement=Measurement(
            name=Term(original="Top-1 Accuracy"), unit=Term(original="percent")
        ),
        result=Result(
            direction=ResultDirection.OBSERVED, value=76.1, unit=Term(original="percent")
        ),
        evidence_span=claim.evidence_span,
    )


def test_normalize_claim_fills_every_canonical_and_keeps_every_original() -> None:
    raw = _raw_claim()

    claim = normalize_claim(raw, get_profile(Domain.COMPUTER_SCIENCE))

    assert claim.subject == Term(original="ResNet 50", canonical="ResNet-50")
    assert claim.method is not None
    assert claim.method.name == Term(original="Label  Smoothing", canonical="label smoothing")
    assert claim.comparator is not None
    assert claim.comparator.name.canonical == "vgg-16 baseline"
    assert claim.measurement is not None and claim.measurement.unit is not None
    assert claim.measurement.name.canonical == "top-1 accuracy"
    assert claim.measurement.unit == Term(original="percent", canonical="%")
    assert claim.result.unit == Term(original="percent", canonical="%")
    assert claim.evidence_span == raw.evidence_span
    assert raw.subject.canonical is None


def test_normalize_claim_keeps_a_canonical_that_is_already_set() -> None:
    claim = computer_science_paper().claim

    assert normalize_claim(claim, get_profile(Domain.COMPUTER_SCIENCE)) == claim


def test_normalize_claim_handles_absent_parts() -> None:
    raw = _raw_claim().model_copy(update={"method": None, "comparator": None, "measurement": None})

    claim = normalize_claim(raw, get_profile(Domain.COMPUTER_SCIENCE))

    assert (claim.method, claim.comparator, claim.measurement) == (None, None, None)
    assert claim.subject.canonical == "ResNet-50"
