import pytest

from evidence_dossier.ingest import PUBMED_DOMAIN, arxiv_category_domain, pubmed_domain
from evidence_dossier.model import Domain


@pytest.mark.parametrize(
    ("category", "domain"),
    [
        ("cs.LG", Domain.COMPUTER_SCIENCE),
        ("cs.CL", Domain.COMPUTER_SCIENCE),
        ("physics.optics", Domain.PHYSICS),
        ("astro-ph.GA", Domain.PHYSICS),
        ("cond-mat.mtrl-sci", Domain.PHYSICS),
        ("quant-ph", Domain.PHYSICS),
        ("math.CO", Domain.MATHEMATICS),
        ("stat.ML", Domain.MATHEMATICS),
        ("q-bio.NC", Domain.BIOLOGY),
        ("eess.SP", Domain.ENGINEERING),
        ("physics.chem-ph", Domain.CHEMISTRY),
        ("hep-th", Domain.OTHER_STEM),
        ("econ.EM", Domain.OTHER_STEM),
    ],
)
def test_arxiv_primary_category_maps_to_a_domain(category: str, domain: Domain) -> None:
    assert arxiv_category_domain(category) == domain


def test_pubmed_works_are_biology_by_default() -> None:
    assert PUBMED_DOMAIN == Domain.BIOLOGY
    assert pubmed_domain([]) == Domain.BIOLOGY
    assert pubmed_domain(["Neurons", "Mice"]) == Domain.BIOLOGY


def test_chemistry_headings_without_biology_headings_give_chemistry() -> None:
    assert pubmed_domain(["Catalysis", "Nickel"]) == Domain.CHEMISTRY
    assert pubmed_domain([" catalysis ", "CHEMISTRY, ORGANIC"]) == Domain.CHEMISTRY


def test_a_biology_heading_keeps_the_biology_profile() -> None:
    # The work loses its organism and assay fields under the chemistry profile (ADR 0010).
    assert pubmed_domain(["Photochemistry", "Cells, Cultured", "Humans"]) == Domain.BIOLOGY
