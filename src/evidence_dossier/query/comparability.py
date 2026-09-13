"""Comparability engine: does a claim address the proposition (plan sections 37 and 38)?

Each generic dimension gets a match flag and a one sentence reason. A term
matches when at least MATCH_THRESHOLD of the proposition tokens appear in the
claim term, on the canonical form or on the original text, whichever scores
higher. The profile's comparability features decide which claim fields count
as conditions.
"""

from evidence_dossier.model import (
    BiologyAttributes,
    ChemistryAttributes,
    ClaimType,
    ComparabilityLevel,
    ComputerScienceAttributes,
    EngineeringAttributes,
    EvidenceClaim,
    FrozenModel,
    PhysicsAttributes,
    QueryProposition,
    Term,
)
from evidence_dossier.profiles import DomainProfile
from evidence_dossier.query.text import overlap

# Share of proposition tokens that a claim term must hold. Half, so a two word
# measurement such as "factual hallucination" still matches "factual error rate".
MATCH_THRESHOLD = 0.5

# Profile feature name to the claim attribute that reports it (plan section 38).
# Features that map onto the subject, comparator or measurement have their own dimension.
_FEATURE_FIELDS: dict[str, str] = {
    "task": "task",
    "dataset": "dataset",
    "benchmark": "benchmark",
    "model family": "model",
    "hardware": "hardware",
    "evaluation conditions": "evaluation_metric",
    "intervention": "intervention",
    "organism": "organism",
    "model": "disease_model",
    "dose context": "dose",
    "catalyst": "catalyst",
    "substrate": "compound",
    "conditions": "temperature",
    # Physics and engineering (ADR 0011). system and material name a generic
    # ResearchContext field that holds a string, so they read the generic value first
    # and the attribute value second. theoretical_assumptions names a generic field
    # too, but that one holds a tuple, and _condition_value takes a string, so this
    # key always reads the attribute value. The rest name no generic field at all and
    # read the attribute value.
    "system": "system",
    "sample": "sample",
    "apparatus": "apparatus",
    "theoretical assumptions": "theoretical_assumptions",
    "component": "component",
    "material": "material",
    "load": "load",
    "operating conditions": "operating_conditions",
    "standard": "standard",
}


class DimensionResult(FrozenModel):
    """One comparability dimension with its verdict and the reason for it."""

    dimension: str
    matched: bool
    reason: str


class ComparabilityAssessment(FrozenModel):
    """The dimension results for one claim against one proposition, and the overall level."""

    level: ComparabilityLevel
    dimensions: tuple[DimensionResult, ...]

    def matched(self, dimension: str) -> bool:
        return any(result.matched for result in self.dimensions if result.dimension == dimension)

    def reasons(self) -> tuple[str, ...]:
        return tuple(result.reason for result in self.dimensions)


class ComparabilityEngine:
    """Scores the generic dimensions and derives the overall level."""

    def assess(
        self, proposition: QueryProposition, claim: EvidenceClaim, profile: DomainProfile
    ) -> ComparabilityAssessment:
        dimensions = (
            _subject(proposition, claim),
            _method(proposition, claim),
            _context(proposition, claim),
            _comparator(proposition, claim),
            _measurement(proposition, claim),
            _conditions(proposition, claim, profile),
            _directness(proposition, claim),
        )
        matched = {result.dimension for result in dimensions if result.matched}
        return ComparabilityAssessment(level=_level(matched), dimensions=dimensions)


def _level(matched: set[str]) -> ComparabilityLevel:
    if len(matched) == 7:
        return ComparabilityLevel.EXACT
    if "subject" not in matched:
        return ComparabilityLevel.INCOMPATIBLE
    if "measurement" not in matched:
        return ComparabilityLevel.LOW
    if "comparator" in matched:
        return ComparabilityLevel.HIGH
    return ComparabilityLevel.MODERATE


def _term_overlap(query_text: str | None, term: Term | None) -> float:
    if term is None:
        return 0.0
    return max(overlap(query_text, term.canonical), overlap(query_text, term.original))


def _label(term: Term | None) -> str:
    return "nothing" if term is None else f"'{term.canonical or term.original}'"


def _subject(proposition: QueryProposition, claim: EvidenceClaim) -> DimensionResult:
    score = _term_overlap(proposition.subject, claim.subject)
    matched = score >= MATCH_THRESHOLD
    return DimensionResult(
        dimension="subject",
        matched=matched,
        reason=(
            f"The claim subject {_label(claim.subject)} {'holds' if matched else 'lacks'}"
            f" the proposition subject '{proposition.subject}' (overlap {score:.2f})."
        ),
    )


def _method(proposition: QueryProposition, claim: EvidenceClaim) -> DimensionResult:
    if claim.method is None:
        return DimensionResult(
            dimension="method", matched=True, reason="The claim names no method to compare."
        )
    score = _term_overlap(proposition.subject, claim.method.name)
    matched = score >= MATCH_THRESHOLD
    return DimensionResult(
        dimension="method",
        matched=matched,
        reason=(
            f"The claim method {_label(claim.method.name)} {'holds' if matched else 'lacks'}"
            f" the proposition subject (overlap {score:.2f})."
        ),
    )


def _context(proposition: QueryProposition, claim: EvidenceClaim) -> DimensionResult:
    context = claim.research_context
    if proposition.domain is not None and proposition.domain is not context.domain:
        return DimensionResult(
            dimension="context",
            matched=False,
            reason=f"The claim domain {context.domain} differs from the proposition domain {proposition.domain}.",
        )
    wanted = {
        "dataset": (proposition.dataset, context.dataset),
        "system": (proposition.system, context.system),
        "population": (proposition.population, context.population),
    }
    unmet = [
        name
        for name, (query_value, claim_value) in wanted.items()
        if query_value is not None
        and (claim_value is None or query_value.lower() != claim_value.lower())
    ]
    if unmet:
        return DimensionResult(
            dimension="context",
            matched=False,
            reason=f"The claim context does not meet the proposition filter on {', '.join(unmet)}.",
        )
    return DimensionResult(
        dimension="context",
        matched=True,
        reason=f"The claim context in domain {context.domain} meets every proposition filter.",
    )


def _comparator(proposition: QueryProposition, claim: EvidenceClaim) -> DimensionResult:
    if proposition.comparator is None and claim.comparator is None:
        return DimensionResult(
            dimension="comparator", matched=True, reason="Neither side names a comparator."
        )
    if proposition.comparator is None or claim.comparator is None:
        side = "proposition" if proposition.comparator is None else "claim"
        return DimensionResult(
            dimension="comparator",
            matched=False,
            reason=f"The {side} names no comparator, so the comparator dimension is open.",
        )
    score = _term_overlap(proposition.comparator, claim.comparator.name)
    matched = score >= MATCH_THRESHOLD
    return DimensionResult(
        dimension="comparator",
        matched=matched,
        reason=(
            f"The claim comparator {_label(claim.comparator.name)} {'holds' if matched else 'lacks'}"
            f" the proposition comparator '{proposition.comparator}' (overlap {score:.2f})."
        ),
    )


def _measurement(proposition: QueryProposition, claim: EvidenceClaim) -> DimensionResult:
    """The claim outcome or its measurement name must hold the proposition measurement."""
    if proposition.measurement is None:
        return DimensionResult(
            dimension="measurement",
            matched=False,
            reason="The proposition names no measurement, so the measurement dimension is open.",
        )
    name = None if claim.measurement is None else claim.measurement.name
    score = max(
        overlap(proposition.measurement, claim.outcome),
        _term_overlap(proposition.measurement, name),
    )
    matched = score >= MATCH_THRESHOLD
    return DimensionResult(
        dimension="measurement",
        matched=matched,
        reason=(
            f"The claim outcome '{claim.outcome}' or measurement {_label(name)}"
            f" {'holds' if matched else 'lacks'} the proposition measurement"
            f" '{proposition.measurement}' (overlap {score:.2f})."
        ),
    )


def _conditions(
    proposition: QueryProposition, claim: EvidenceClaim, profile: DomainProfile
) -> DimensionResult:
    """The profile's comparability features decide which claim fields count as conditions."""
    reported = {
        feature: value
        for feature in profile.comparability_features
        if (field := _FEATURE_FIELDS.get(feature)) is not None
        and (value := _condition_value(claim, field)) is not None
    }
    wanted = {"dataset": proposition.dataset}
    unmet = [
        feature
        for feature, query_value in wanted.items()
        if query_value is not None
        and feature in reported
        and query_value.lower() != reported[feature].lower()
    ]
    named = ", ".join(reported) if reported else "no profile condition"
    if unmet:
        return DimensionResult(
            dimension="conditions",
            matched=False,
            reason=f"The claim reports {', '.join(unmet)} against the proposition filter under the {profile.domain} profile.",
        )
    return DimensionResult(
        dimension="conditions",
        matched=True,
        reason=f"The claim reports {named} under the {profile.domain} profile, and no proposition filter disagrees.",
    )


def _condition_value(claim: EvidenceClaim, field: str) -> str | None:
    context = claim.research_context
    generic = getattr(context, field, None)
    if isinstance(generic, str):
        return generic
    # Every member of the closed union, or a new profile's fields stay unread here.
    for holder in (context, claim.method, claim.comparator):
        attributes = None if holder is None else holder.domain_attributes
        if isinstance(
            attributes,
            BiologyAttributes
            | ComputerScienceAttributes
            | ChemistryAttributes
            | PhysicsAttributes
            | EngineeringAttributes,
        ):
            value = getattr(attributes, field, None)
            if isinstance(value, str):
                return value
    return None


def _directness(proposition: QueryProposition, claim: EvidenceClaim) -> DimensionResult:
    """Direct evidence measures the proposition measurement itself, in an empirical claim."""
    name = None if claim.measurement is None else claim.measurement.name
    score = _term_overlap(proposition.measurement, name)
    empirical = claim.claim_type is not ClaimType.THEORETICAL
    matched = score >= MATCH_THRESHOLD and empirical
    if not empirical:
        reason = f"The claim is {claim.claim_type}, so it measures nothing directly."
    elif matched:
        reason = (
            f"The claim measures {_label(name)}, which names the proposition measurement directly."
        )
    else:
        reason = (
            f"The claim measures {_label(name)}, which does not name the proposition"
            f" measurement '{proposition.measurement}' (overlap {score:.2f})."
        )
    return DimensionResult(dimension="evidence directness", matched=matched, reason=reason)
