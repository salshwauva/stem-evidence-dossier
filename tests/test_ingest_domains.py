import pytest

from evidence_dossier.ingest import PUBMED_DOMAIN, arxiv_category_domain
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
        ("hep-th", Domain.OTHER_STEM),
        ("econ.EM", Domain.OTHER_STEM),
    ],
)
def test_arxiv_primary_category_maps_to_a_domain(category: str, domain: Domain) -> None:
    assert arxiv_category_domain(category) == domain


def test_pubmed_works_are_biology() -> None:
    assert PUBMED_DOMAIN == Domain.BIOLOGY
