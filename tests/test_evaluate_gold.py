"""The gold loader on the dev fixture, and the split invariants."""

import pytest

from evidence_dossier.evaluate import Dataset, DatasetSplitter, GoldDocument
from evidence_dossier.model import SourceLevel, WorkLink, WorkLinkRelation
from tests.evaluate_predictions import B1, B2, C1, C2, fixture_dataset


def test_loader_reads_the_fixture_in_name_order() -> None:
    dataset = fixture_dataset()
    assert dataset.split == "dev"
    assert [d.research_work_id for d in dataset.documents] == [B1, B2, C1, C2]
    assert len(dataset.claims) == 7
    assert [q.query_id for q in dataset.retrievals] == ["q1", "q2", "q3"]
    assert len(dataset.stances) == 9
    assert dataset.documents[1].source_level is SourceLevel.ABSTRACT_ONLY
    assert dataset.claims[0].claim_key == f"{B1}:c1"


def test_restrict_keeps_the_labels_of_the_given_works_only() -> None:
    dataset = fixture_dataset().restrict(frozenset({C1}))
    assert [d.research_work_id for d in dataset.documents] == [C1]
    assert {q.query_id: q.relevant_claim_ids for q in dataset.retrievals} == {
        "q1": frozenset(),
        "q2": frozenset({f"{C1}:c1"}),
        "q3": frozenset(),
    }
    assert {(s.query_id, s.claim_id) for s in dataset.stances} == {
        ("q2", f"{C1}:c1"),
        ("q2", f"{C1}:c2"),
        ("q3", f"{C1}:c1"),
    }


def test_gold_document_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError):
        GoldDocument.model_validate(
            {"research_work_id": B1, "document_id": "d", "source_level": "FULL_TEXT", "x": 1}
        )


WORKS = [f"work_{n:04d}" for n in range(200)]


def test_split_is_stable_across_instances_and_runs() -> None:
    first = DatasetSplitter().assign(WORKS)
    second = DatasetSplitter().assign(reversed(WORKS))
    assert first == second
    assert set(first.values()) == {"dev", "test"}
    # The hash is fixed, so a known work keeps its side across releases.
    assert first["work_0000"] == "test"
    assert first["work_0001"] == "dev"


def test_linked_works_share_a_side() -> None:
    links = [
        WorkLink(source_work_id="a", relation=WorkLinkRelation.PREPRINT_OF, target_work_id="b"),
        WorkLink(source_work_id="b", relation=WorkLinkRelation.VERSION_OF, target_work_id="c"),
        WorkLink(source_work_id="d", relation=WorkLinkRelation.DUPLICATE_OF, target_work_id="c"),
    ]
    joined = {len({sides[w] for w in "abcd"}) for sides in _assignments(links)}
    apart = {len({sides[w] for w in "abcd"}) for sides in _assignments([])}
    assert joined == {1}
    assert 2 in apart


def _assignments(links: list[WorkLink]) -> list[dict[str, str]]:
    return [
        dict(DatasetSplitter(dev_ratio=0.5, salt=salt).assign(["a", "b", "c", "d", "e"], links))
        for salt in ("s1", "s2", "s3", "s4", "s5", "s6")
    ]


def test_split_ratio_bounds() -> None:
    assert set(DatasetSplitter(dev_ratio=1.0).assign(WORKS).values()) == {"dev"}
    assert set(DatasetSplitter(dev_ratio=0.0).assign(WORKS).values()) == {"test"}
    with pytest.raises(ValueError):
        DatasetSplitter(dev_ratio=1.5)


def test_split_ratio_holds_roughly() -> None:
    sides = DatasetSplitter(dev_ratio=0.7).assign(WORKS)
    dev = sum(side == "dev" for side in sides.values())
    assert 0.6 * len(WORKS) <= dev <= 0.8 * len(WORKS)


def test_dataset_split_literal() -> None:
    with pytest.raises(ValueError):
        Dataset.model_validate({"split": "train"})
