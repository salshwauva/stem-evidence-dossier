import json

import pytest

from evidence_dossier.extract import PROMPT_VERSION, CandidateClaims, build_prompt
from evidence_dossier.extract.prompt import DATA_TEXT, SECTION_BEGIN, SECTION_END, TASK_TEXT
from evidence_dossier.model import Domain
from evidence_dossier.profiles import get_profile
from evidence_dossier.store import Store
from tests.extract_support import DISCUSSION_TEXT, RESULTS_TEXT, add_paper, paper_corpus


def test_prompt_states_the_version_the_schema_and_the_rules() -> None:
    with Store(":memory:") as store:
        corpus = paper_corpus(store)

    assert PROMPT_VERSION == "claims-v1"
    assert f"Prompt version: {PROMPT_VERSION}" in corpus.prompt
    assert json.dumps(CandidateClaims.model_json_schema(), sort_keys=True) in corpus.prompt
    assert TASK_TEXT in corpus.prompt
    assert DATA_TEXT in corpus.prompt


def test_prompt_wraps_every_section_as_data_in_document_order() -> None:
    with Store(":memory:") as store:
        corpus = paper_corpus(store)
    first, second = corpus.sections

    body = corpus.prompt[corpus.prompt.index(DATA_TEXT) :]
    expected = (
        SECTION_BEGIN.format(section_id=first.id, section_type="RESULTS"),
        RESULTS_TEXT,
        SECTION_END.format(section_id=first.id),
        SECTION_BEGIN.format(section_id=second.id, section_type="DISCUSSION"),
        DISCUSSION_TEXT,
        SECTION_END.format(section_id=second.id),
    )
    positions = [body.index(part) for part in expected]
    assert positions == sorted(positions)


@pytest.mark.parametrize(
    ("domain", "entity", "field"),
    [
        (Domain.COMPUTER_SCIENCE, "evaluation metric", "compute_budget"),
        (Domain.BIOLOGY, "cell line", "disease_model"),
        (Domain.CHEMISTRY, "reaction time", "yield"),
    ],
)
def test_profile_adds_its_entities_and_attribute_fields(
    domain: Domain, entity: str, field: str
) -> None:
    with Store(":memory:") as store:
        corpus = add_paper(store, "2409.00003", (RESULTS_TEXT,), domain=domain)
    profile = get_profile(domain)
    assert profile.attribute_model is not None
    tag = profile.attribute_model.model_fields["profile"].default

    assert f"Domain profile: {domain.value}" in corpus.prompt
    assert entity in corpus.prompt
    assert f'profile tag "{tag}"' in corpus.prompt
    assert field in corpus.prompt
    assert "profile, " not in corpus.prompt


def test_generic_profile_tells_the_model_to_leave_attributes_null() -> None:
    # Mathematics keeps the generic profile. Physics carries its own since ADR 0011.
    with Store(":memory:") as store:
        corpus = add_paper(store, "2409.00004", (RESULTS_TEXT,), domain=Domain.MATHEMATICS)

    assert "Leave domain_attributes null" in corpus.prompt
    assert "Expected entities" not in corpus.prompt


def test_prompt_changes_when_the_sections_change() -> None:
    with Store(":memory:") as store:
        corpus = paper_corpus(store)
    profile = get_profile(Domain.COMPUTER_SCIENCE)

    assert build_prompt(corpus.document, corpus.sections[:1], profile) != corpus.prompt
