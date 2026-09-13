"""Physics and engineering reach their own profiles, and the engine reads those profiles.

Every work, passage and value here is invented for the tests.
"""

import pytest

from evidence_dossier.ingest.domains import arxiv_category_domain
from evidence_dossier.model import (
    BiologyAttributes,
    ChemistryAttributes,
    ClaimType,
    ComparabilityLevel,
    Comparator,
    ComputerScienceAttributes,
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
    GENERIC_COMPARABILITY_DIMENSIONS,
    DomainProfile,
    EngineeringProfile,
    PhysicsProfile,
    get_profile,
)
from evidence_dossier.query.comparability import (
    _FEATURE_FIELDS,
    ComparabilityAssessment,
    ComparabilityEngine,
)

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


def _physics_context(*, typed: bool, system: bool = True) -> ResearchContext:
    """The same physics context with and without its typed attributes.

    system also drops out on request. The physics profile reads that feature off
    the generic record, not off the attribute class, so the two switches separate
    what each source contributes.
    """
    return ResearchContext(
        domain=Domain.PHYSICS,
        system="rectangular waveguide" if system else None,
        material="split ring metamaterial",
        domain_attributes=PhysicsAttributes(
            apparatus="rectangular waveguide",
            sample="split ring metamaterial",
            temperature="4 K",
            field_strength="0.2 T",
            wavelength="30 mm",
            instrument="vector network analyser",
            theoretical_assumptions="effective medium below 15 GHz",
        )
        if typed
        else None,
    )


def _physics_claim(*, typed: bool = True, system: bool = True) -> EvidenceClaim:
    return _claim(
        "metamaterial",
        passage=PHYSICS_PASSAGE,
        context=_physics_context(typed=typed, system=system),
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


def test_the_engine_reads_physics_fields_because_the_physics_profile_names_them() -> None:
    """Every mapped physics feature reports, and every one of them drops out on demand.

    Four come off PhysicsAttributes: sample, apparatus, temperature for the conditions
    feature, and theoretical assumptions. The fifth, system, comes off the generic
    record. Removing the attributes leaves system alone. Removing the generic value
    too leaves nothing, so all five are accounted for and none reports by accident.
    """
    proposition = _physics_proposition()
    physics = get_profile(Domain.PHYSICS)
    mapped = tuple(
        feature for feature in physics.comparability_features if feature in _FEATURE_FIELDS
    )

    typed = _conditions_reason(_assess(proposition, _physics_claim(), physics))
    untyped = _conditions_reason(_assess(proposition, _physics_claim(typed=False), physics))
    bare = _assess(proposition, _physics_claim(typed=False, system=False), physics)
    other_profile = _assess(proposition, _physics_claim(), get_profile(Domain.COMPUTER_SCIENCE))

    assert mapped == ("system", "sample", "apparatus", "conditions", "theoretical assumptions")
    assert f"The claim reports {', '.join(mapped)} under the PHYSICS" in typed
    assert "The claim reports system under the PHYSICS profile" in untyped
    assert "no profile condition" in _conditions_reason(bare)
    # A profile that names none of those features reads the same claim off nothing.
    assert not set(physics.comparability_features) & set(
        get_profile(Domain.COMPUTER_SCIENCE).comparability_features
    )
    assert "no profile condition" in _conditions_reason(other_profile)


def test_the_engine_reads_engineering_fields_because_the_profile_names_them() -> None:
    """The claim carries five features on EngineeringAttributes and two on the context."""
    proposition = _engineering_proposition()
    engineering = get_profile(Domain.ENGINEERING)

    typed = _conditions_reason(_assess(proposition, _engineering_claim(), engineering))
    untyped = _conditions_reason(_assess(proposition, _engineering_claim(typed=False), engineering))
    other_profile = _assess(proposition, _engineering_claim(), get_profile(Domain.BIOLOGY))

    assert (
        "The claim reports system, component, material, load, operating conditions,"
        " standard, hardware under the ENGINEERING" in typed
    )
    assert "The claim reports system, hardware under the ENGINEERING profile" in untyped
    assert not set(engineering.comparability_features) & set(
        get_profile(Domain.BIOLOGY).comparability_features
    )
    assert "no profile condition" in _conditions_reason(other_profile)


def test_a_physics_claim_and_a_physics_proposition_reach_a_comparability_level() -> None:
    """A physics pair runs the whole engine, not only the conditions dimension."""
    assessment = _assess(_physics_proposition(), _physics_claim(), get_profile(Domain.PHYSICS))

    assert assessment.matched("subject")
    assert assessment.matched("measurement")
    assert assessment.matched("conditions")
    assert assessment.level is not ComparabilityLevel.INCOMPATIBLE


# A declared comparability feature reaches the engine only through _FEATURE_FIELDS,
# which maps the feature name to the claim field that reports it. The split below is
# the whole picture, per profile, in the order each profile declares its features.
#
# An unread name is one of two things. A name in GENERIC_COMPARABILITY_DIMENSIONS has
# its own dimension function, so the engine assesses it directly and the table needs no
# entry for it. Every other unread name is the gap that ADR 0011 records: biology
# target and endpoint, chemistry reaction, and computer science baseline and metric
# have no claim field to read. An entry for those would change comparability, and so
# stance, for three domains that ADR 0011 does not touch.
#
# This test exists so the gap cannot grow in silence when someone adds a profile or a
# feature name.
KNOWN_FEATURE_GAP = frozenset({"target", "endpoint", "reaction", "baseline", "metric"})

GENERIC_SPLIT = (
    ("conditions",),
    ("subject", "method", "context", "comparator", "measurement", "evidence directness"),
)

# Domain to (features the engine reads through the table, features it does not).
FEATURE_SPLIT: dict[Domain, tuple[tuple[str, ...], tuple[str, ...]]] = {
    Domain.BIOLOGY: (
        ("intervention", "organism", "model", "dose context"),
        ("target", "endpoint"),
    ),
    Domain.CHEMISTRY: (
        ("catalyst", "substrate", "conditions"),
        ("reaction", "measurement"),
    ),
    Domain.COMPUTER_SCIENCE: (
        ("task", "dataset", "model family", "hardware", "evaluation conditions"),
        ("baseline", "metric"),
    ),
    Domain.PHYSICS: (
        ("system", "sample", "apparatus", "conditions", "theoretical assumptions"),
        ("measurement",),
    ),
    Domain.ENGINEERING: (
        ("system", "component", "material", "load", "operating conditions", "standard", "hardware"),
        ("measurement",),
    ),
    Domain.MATHEMATICS: GENERIC_SPLIT,
    Domain.MULTIDISCIPLINARY: GENERIC_SPLIT,
    Domain.OTHER_STEM: GENERIC_SPLIT,
}


@pytest.mark.parametrize("domain", list(Domain))
def test_the_feature_table_covers_the_features_each_profile_declares(domain: Domain) -> None:
    features = get_profile(domain).comparability_features
    read = tuple(feature for feature in features if feature in _FEATURE_FIELDS)
    unread = tuple(feature for feature in features if feature not in _FEATURE_FIELDS)
    expected_read, expected_unread = FEATURE_SPLIT[domain]

    assert read == expected_read
    assert unread == expected_unread
    for feature in unread:
        assert feature in GENERIC_COMPARABILITY_DIMENSIONS or feature in KNOWN_FEATURE_GAP


@pytest.mark.parametrize("domain", list(Domain))
def test_every_mapped_feature_names_a_field_that_some_record_declares(domain: Domain) -> None:
    """A mapped feature whose field exists nowhere would report a condition for no claim."""
    read, _ = FEATURE_SPLIT[domain]
    declared = set(ResearchContext.model_fields)
    for cls in (
        BiologyAttributes,
        ChemistryAttributes,
        ComputerScienceAttributes,
        PhysicsAttributes,
        EngineeringAttributes,
    ):
        declared |= set(cls.model_fields)

    for feature in read:
        assert _FEATURE_FIELDS[feature] in declared, feature
