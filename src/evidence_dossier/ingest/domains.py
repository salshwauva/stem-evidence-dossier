"""Domain detection from source metadata (plan section 28).

Version 1 reads the domain off the source. An arXiv primary category maps to
a Domain by its archive prefix, with one category level rule for chemical
physics. A PubMed work is BIOLOGY unless its MeSH headings meet the narrow
chemistry rule below (ADR 0010).
"""

from collections.abc import Iterable

from evidence_dossier.model import Domain

PUBMED_DOMAIN = Domain.BIOLOGY

# arXiv has no chemistry archive. physics.chem-ph is chemical physics, a physics
# category, and mapping it to CHEMISTRY is a judgment call that ADR 0010 records.
# The rule fires on the primary category only.
_ARXIV_CATEGORIES: dict[str, Domain] = {
    "physics.chem-ph": Domain.CHEMISTRY,
}

# arXiv archive (the part before the dot) to domain. A category without a dot,
# such as "hep-th" or "quant-ph", is its own archive.
_ARXIV_ARCHIVES: dict[str, Domain] = {
    "cs": Domain.COMPUTER_SCIENCE,
    "physics": Domain.PHYSICS,
    "astro-ph": Domain.PHYSICS,
    "cond-mat": Domain.PHYSICS,
    "quant-ph": Domain.PHYSICS,
    "math": Domain.MATHEMATICS,
    "stat": Domain.MATHEMATICS,
    "q-bio": Domain.BIOLOGY,
    "eess": Domain.ENGINEERING,
}

# MeSH descriptor names, compared case insensitively. A work takes CHEMISTRY
# only when at least one chemistry heading is present and no biology heading
# is, so a biology paper with chemistry subject matter keeps the biology
# profile and its organism and assay fields (ADR 0010). MeSH describes subject
# matter, not method, so the rule stays small.
CHEMISTRY_MESH_HEADINGS: frozenset[str] = frozenset(
    {
        "catalysis",
        "chemistry",
        "chemistry, organic",
        "chemistry, physical",
        "chemistry, inorganic",
        "chemical synthesis",
        "electrochemistry",
        "photochemistry",
        "chemistry techniques, synthetic",
    }
)
BIOLOGY_MESH_HEADINGS: frozenset[str] = frozenset(
    {
        "animals",
        "humans",
        "mice",
        "rats",
        "cell line",
        "cells, cultured",
        "proteins",
        "genes",
        "gene expression",
        "organisms",
        "biological assay",
    }
)


def arxiv_category_domain(primary_category: str) -> Domain:
    """Return the domain for an arXiv primary category such as "cs.LG" or "astro-ph.GA".

    An archive that the table does not name gives OTHER_STEM.
    """
    category = _ARXIV_CATEGORIES.get(primary_category)
    if category is not None:
        return category
    archive = primary_category.split(".", 1)[0]
    return _ARXIV_ARCHIVES.get(archive, Domain.OTHER_STEM)


def pubmed_domain(mesh_headings: Iterable[str]) -> Domain:
    """Return CHEMISTRY when the headings meet the chemistry rule, else PUBMED_DOMAIN."""
    folded = {heading.strip().lower() for heading in mesh_headings}
    if folded & CHEMISTRY_MESH_HEADINGS and not folded & BIOLOGY_MESH_HEADINGS:
        return Domain.CHEMISTRY
    return PUBMED_DOMAIN
