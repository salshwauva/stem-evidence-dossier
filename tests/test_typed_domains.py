"""Physics and engineering reach their own profiles, and the engine reads those profiles.

Every work, passage and value here is invented for the tests.
"""

import pytest

from evidence_dossier.ingest.domains import arxiv_category_domain
from evidence_dossier.model import (
    ClaimType,
    ComparabilityLevel,
    Comparator,
    Domain,
    EngineeringAttributes,
    EvidenceClaim,
    EvidenceSpan,
    Measurement,
    Method,
    PhysicsAttributes,
    QueryProposition,
    ResearchContext,
    Result,
    ResultDirection,
    Term,
)
from evidence_dossier.profiles import (
    DomainProfile,
    EngineeringProfile,
    PhysicsProfile,
    get_profile,
)
from evidence_dossier.query.comparability import ComparabilityAssessment, ComparabilityEngine

PHYSICS_PASSAGE = "The patterned sample showed a negative refractive index at 10 GHz"
ENGINEERING_PASSAGE = "The redesigned rotor raised drive efficiency to 94% from 88%"


def _claim(
    key: str,
    *,
    passage: str,
    context: ResearchContext,
    subject: str,
    outcome: str,
    measurement: str,
    comparator: str,
    method: Method,
    direction: ResultDirection,
    claim_type: ClaimType,
) -> EvidenceClaim:
    return EvidenceClaim(
        id=f"claim-{key}",
        research_work_id=f"work-{key}",
        study_id=f"study-{key}",
        claim_type=claim_type,
        claim_text=passage,
        subject=Term(original=subject),
        predicate=direction.value.lower(),
        outcome=outcome,
        research_context=context,
        method=method,
        comparator=Comparator(name=Term(original=comparator)),
        measurement=Measurement(name=Term(original=measurement)),
        result=Result(direction=direction),
        evidence_span=EvidenceSpan(
            research_work_id=f"work-{key}",
            section_id=f"work-{key}_v1_s0",
            start_offset=0,
            end_offset=len(passage),
            source_text=passage,
        ),
    )


def _physics_context(*, typed: bool) -> ResearchContext:
    """The same physics context with and without its typed attributes."""
    return ResearchContext(
        domain=Domain.PHYSICS,
        system="rectangular waveguide",
        material="split ring metamaterial",
        domain_attributes=PhysicsAttributes(
            apparatus="rectangular waveguide",
            sample="split ring metamaterial",
            temperature="4 K",
            field_strength="0.2 T",
            wavelength="30 mm",
            instrument="vector network analyser",
        )
        if typed
        else None,
    )


def _physics_claim(*, typed: bool = True) -> EvidenceClaim:
    return _claim(
        "metamaterial",
        passage=PHYSICS_PASSAGE,
        context=_physics_context(typed=typed),
        subject="split ring metamaterial",
        outcome="refractive index",
        measurement="refractive index",
        comparator="unpatterned copper film",
        method=Method(name=Term(original="waveguide transmission measurement")),
        direction=ResultDirection.OBSERVED,
        claim_type=ClaimType.PROPERTY,
    )


def _physics_proposition() -> QueryProposition:
    return QueryProposition(
        id="query-metamaterial",
        text="split ring metamaterial shows a negative refractive index at microwave frequencies",
        domain=Domain.PHYSICS,
        subject="split ring metamaterial",
        relationship="shows",
        measurement="refractive index",
        comparator="unpatterned copper film",
    )


def _engineering_claim(*, typed: bool = True) -> EvidenceClaim:
    context = ResearchContext(
        domain=Domain.ENGINEERING,
        system="induction motor drive",
        hardware="3 kW induction motor test rig",
        domain_attributes=EngineeringAttributes(
            system="induction motor drive",
            component="rotor",
            material="laminated silicon steel",
            load="rated torque",
            operating_conditions="40 C ambient",
            standard="IEC 60034-2-1",
            test_method="dynamometer test",
            duty_cycle="continuous",
            tolerance="plus or minus 0.5%",
        )
        if typed
        else None,
    )
    return _claim(
        "rotor",
        passage=ENGINEERING_PASSAGE,
        context=context,
        subject="redesigned rotor",
        outcome="drive efficiency",
        measurement="efficiency",
        comparator="baseline rotor",
        method=Method(name=Term(original="dynamometer test")),
        direction=ResultDirection.IMPROVED,
        claim_type=ClaimType.PERFORMANCE,
    )


def _engineering_proposition() -> QueryProposition:
    return QueryProposition(
        id="query-rotor",
        text="a redesigned rotor improves drive efficiency against a baseline rotor",
        domain=Domain.ENGINEERING,
        subject="redesigned rotor",
        relationship="improves",
        measurement="efficiency",
        comparator="baseline rotor",
    )


def _conditions_reason(assessment: ComparabilityAssessment) -> str:
    (reason,) = [
        result.reason for result in assessment.dimensions if result.dimension == "conditions"
    ]
    return reason


def _assess(
    proposition: QueryProposition, claim: EvidenceClaim, profile: DomainProfile
) -> ComparabilityAssessment:
    return ComparabilityEngine().assess(proposition, claim, profile)


# Decision 6: the detected domain reaches the typed profile.


@pytest.mark.parametrize("category", ["cond-mat.mtrl-sci", "astro-ph.GA", "quant-ph"])
def test_an_arxiv_physics_category_reaches_the_physics_profile(category: str) -> None:
    domain = arxiv_category_domain(category)

    assert domain is Domain.PHYSICS
    assert isinstance(get_profile(domain), PhysicsProfile)


@pytest.mark.parametrize("category", ["eess.SP", "eess.SY"])
def test_an_arxiv_eess_category_reaches_the_engineering_profile(category: str) -> None:
    domain = arxiv_category_domain(category)

    assert domain is Domain.ENGINEERING
    assert isinstance(get_profile(domain), EngineeringProfile)


def test_a_physics_claim_carries_physics_attributes_through_the_core_model() -> None:
    claim = _physics_claim()

    restored = EvidenceClaim.model_validate_json(claim.model_dump_json())
    attributes = restored.research_context.domain_attributes

    assert isinstance(attributes, PhysicsAttributes)
    assert attributes.profile == "physics"
    assert attributes.temperature == "4 K"
    assert restored == claim


def test_an_engineering_claim_carries_engineering_attributes_through_the_core_model() -> None:
    claim = _engineering_claim()

    restored = EvidenceClaim.model_validate_json(claim.model_dump_json())
    attributes = restored.research_context.domain_attributes

    assert isinstance(attributes, EngineeringAttributes)
    assert attributes.profile == "engineering"
    assert attributes.duty_cycle == "continuous"
    assert restored == claim


# Decision 7: the comparability engine reads what the new profiles hold.


def test_the_engine_reads_a_physics_field_because_the_physics_profile_names_it() -> None:
    """The physics profile lists conditions, and the engine reads it off PhysicsAttributes."""
    proposition = _physics_proposition()
    physics = get_profile(Domain.PHYSICS)

    typed = _conditions_reason(_assess(proposition, _physics_claim(), physics))
    untyped = _conditions_reason(_assess(proposition, _physics_claim(typed=False), physics))
    other_profile = _assess(proposition, _physics_claim(), get_profile(Domain.COMPUTER_SCIENCE))

    assert "conditions" in physics.comparability_features
    assert "The claim reports conditions under the PHYSICS profile" in typed
    # The same claim without its physics attributes reports nothing to compare.
    assert "no profile condition" in untyped
    # A profile that does not name conditions reads the same field off nothing.
    assert "conditions" not in get_profile(Domain.COMPUTER_SCIENCE).comparability_features
    assert "no profile condition" in _conditions_reason(other_profile)


def test_the_engine_reads_an_engineering_field_because_the_profile_names_it() -> None:
    """The engineering profile lists hardware, which the claim reports on its context."""
    proposition = _engineering_proposition()
    engineering = get_profile(Domain.ENGINEERING)

    reported = _conditions_reason(_assess(proposition, _engineering_claim(), engineering))
    other_profile = _assess(proposition, _engineering_claim(), get_profile(Domain.BIOLOGY))

    assert "hardware" in engineering.comparability_features
    assert "The claim reports hardware under the ENGINEERING profile" in reported
    assert "hardware" not in get_profile(Domain.BIOLOGY).comparability_features
    assert "no profile condition" in _conditions_reason(other_profile)


def test_a_physics_claim_and_a_physics_proposition_reach_a_comparability_level() -> None:
    """A physics pair runs the whole engine, not only the conditions dimension."""
    assessment = _assess(_physics_proposition(), _physics_claim(), get_profile(Domain.PHYSICS))

    assert assessment.matched("subject")
    assert assessment.matched("measurement")
    assert assessment.matched("conditions")
    assert assessment.level is not ComparabilityLevel.INCOMPATIBLE
