"""Adversarial regression fixtures (plan section 51).

Each fixture plants text in the paper: an instruction, a fake role line, a
schema change or a fake section delimiter. The reply is what a misled model
might return. The prompt must wrap the planted text as data, and the
validator must reject the reply. These fixtures are regression tests. They
do not show that prompt injection is impossible.
"""

import json
from collections.abc import Iterator

import pytest

from evidence_dossier.extract import extract_document
from evidence_dossier.extract.prompt import DATA_TEXT, SECTION_BEGIN, SECTION_END
from evidence_dossier.model import SectionType, ValidationStatus, make_document_id, make_work_id
from evidence_dossier.normalize import normalize_claim
from evidence_dossier.store import Store
from tests.extract_support import FIXTURES, NOW, add_paper

ADVERSARIAL = sorted(path.stem for path in (FIXTURES / "adversarial").glob("*.json"))


@pytest.fixture
def store() -> Iterator[Store]:
    with Store(":memory:") as opened:
        yield opened


def test_the_fixture_set_holds_five_cases() -> None:
    assert len(ADVERSARIAL) == 5


@pytest.mark.parametrize("name", ADVERSARIAL)
def test_planted_text_is_wrapped_as_data_and_the_reply_is_rejected(store: Store, name: str) -> None:
    fixture = json.loads((FIXTURES / "adversarial" / f"{name}.json").read_text(encoding="utf-8"))
    arxiv_id = f"2409.1{ADVERSARIAL.index(name)}"
    document_id = make_document_id(make_work_id("arxiv", arxiv_id), version=1)
    planted = str(fixture["planted_text"]).replace("{document_id}", document_id)
    corpus = add_paper(store, arxiv_id, (planted,))
    section = corpus.sections[0]
    begin = SECTION_BEGIN.format(section_id=section.id, section_type=SectionType.RESULTS.value)
    end = SECTION_END.format(section_id=section.id)
    reply = str(fixture["response"]).replace("{document_id}", document_id)

    assert corpus.prompt.index(DATA_TEXT) < corpus.prompt.index(begin)
    assert corpus.prompt.index(begin) < corpus.prompt.index(planted) < corpus.prompt.rindex(end)
    run = extract_document(
        corpus.store,
        corpus.document.id,
        corpus.provider(reply),
        normalizer=normalize_claim,
        now=NOW,
    )
    assert run.validation_status is ValidationStatus.INVALID
    assert run.errors
    assert run.raw_response == reply
    assert corpus.store.list_claims() == []
