"""Domain detection from source metadata (plan section 28).

Version 1 reads the domain off the source: an arXiv primary category maps to
a Domain by its archive prefix, and every PubMed work is BIOLOGY.
"""

from evidence_dossier.model import Domain

PUBMED_DOMAIN = Domain.BIOLOGY

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


def arxiv_category_domain(primary_category: str) -> Domain:
    """Return the domain for an arXiv primary category such as "cs.LG" or "astro-ph.GA".

    An archive that the table does not name gives OTHER_STEM.
    """
    archive = primary_category.split(".", 1)[0]
    return _ARXIV_ARCHIVES.get(archive, Domain.OTHER_STEM)
