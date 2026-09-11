import pytest

from evidence_dossier.model import (
    BiologyAttributes,
    ComputerScienceAttributes,
    Domain,
    ResearchContext,
)
from evidence_dossier.profiles import (
    BiologyProfile,
    ComputerScienceProfile,
    GenericProfile,
    get_profile,
)

PROFILED_DOMAINS = {Domain.BIOLOGY, Domain.COMPUTER_SCIENCE}


def test_biology_profile_holds_the_biology_attribute_model() -> None:
    profile = get_profile(Domain.BIOLOGY)

    assert isinstance(profile, BiologyProfile)
    assert profile.domain is Domain.BIOLOGY
    assert profile.attribute_model is BiologyAttributes


def test_computer_science_profile_holds_the_computer_science_attribute_model() -> None:
    profile = get_profile(Domain.COMPUTER_SCIENCE)

    assert isinstance(profile, ComputerScienceProfile)
    assert profile.domain is Domain.COMPUTER_SCIENCE
    assert profile.attribute_model is ComputerScienceAttributes


@pytest.mark.parametrize("domain", [domain for domain in Domain if domain not in PROFILED_DOMAINS])
def test_every_other_domain_falls_back_to_the_generic_profile(domain: Domain) -> None:
    profile = get_profile(domain)

    assert isinstance(profile, GenericProfile)
    assert profile.domain is domain
    assert profile.attribute_model is None


@pytest.mark.parametrize("domain", sorted(PROFILED_DOMAINS))
def test_profile_attribute_model_round_trips_through_the_core_context(domain: Domain) -> None:
    attribute_model = get_profile(domain).attribute_model
    assert attribute_model is not None

    context = ResearchContext(domain=domain, domain_attributes=attribute_model())
    restored = ResearchContext.model_validate_json(context.model_dump_json())

    assert type(restored.domain_attributes) is attribute_model
