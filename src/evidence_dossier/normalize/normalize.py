"""Pure normalization functions over Term and Result (plan section 33).

Every Term keeps its original text. A table hit gives the canonical value.
A name that no table lists gets fold_name as its canonical value, and a unit
that no table lists gets its stripped original. Value conversion between
units, such as 0.1 seconds to 100 ms, is out of scope for this increment.
"""

import re

from evidence_dossier.model import Domain, EvidenceClaim, Term
from evidence_dossier.normalize.tables import NAME_SYNONYMS, UNIT_SYNONYMS
from evidence_dossier.profiles import DomainProfile

_KEY_STRIP = re.compile(r"[\s\-_]+")
_SPACES = re.compile(r"\s+")
_HYPHEN_SPACES = re.compile(r"\s*-\s*")


def fold_key(text: str) -> str:
    """Return the table key of a name or unit: casefolded, without spaces, hyphens or underscores."""
    return _KEY_STRIP.sub("", text.casefold())


def fold_name(text: str) -> str:
    """Return the generic canonical form: casefolded, single spaces, no spaces around hyphens."""
    return _HYPHEN_SPACES.sub("-", _SPACES.sub(" ", text.casefold().strip()))


def canonical_name(text: str, domain: Domain) -> str:
    """Return the canonical name from the domain table, or fold_name when the table has no row."""
    return NAME_SYNONYMS.get(domain, {}).get(fold_key(text), fold_name(text))


def canonical_unit(text: str) -> str:
    """Return the canonical unit from the unit table, or the stripped original."""
    return UNIT_SYNONYMS.get(fold_key(text), text.strip())


def _name(term: Term, domain: Domain) -> Term:
    if term.canonical is not None:
        return term
    return term.model_copy(update={"canonical": canonical_name(term.original, domain)})


def _unit(term: Term | None) -> Term | None:
    if term is None or term.canonical is not None:
        return term
    return term.model_copy(update={"canonical": canonical_unit(term.original)})


def normalize_claim(claim: EvidenceClaim, profile: DomainProfile) -> EvidenceClaim:
    """Return a copy of the claim with every missing canonical value filled.

    A canonical value that is already set stays as it is. The subject, the
    method, comparator and measurement names use the name table of the
    profile domain. The measurement unit and the result unit use the unit table.
    """
    domain = profile.domain
    update: dict[str, object] = {"subject": _name(claim.subject, domain)}
    if claim.method is not None:
        update["method"] = claim.method.model_copy(
            update={"name": _name(claim.method.name, domain)}
        )
    if claim.comparator is not None:
        update["comparator"] = claim.comparator.model_copy(
            update={"name": _name(claim.comparator.name, domain)}
        )
    if claim.measurement is not None:
        update["measurement"] = claim.measurement.model_copy(
            update={
                "name": _name(claim.measurement.name, domain),
                "unit": _unit(claim.measurement.unit),
            }
        )
    update["result"] = claim.result.model_copy(update={"unit": _unit(claim.result.unit)})
    return claim.model_copy(update=update)
