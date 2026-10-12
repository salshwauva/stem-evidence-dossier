import csv
from pathlib import Path

import pytest

from evidence_dossier.evaluate.judge import JudgePair
from evidence_dossier.evaluate.judge_sheet import (
    KEY_COLUMNS,
    SHEET_COLUMNS,
    SheetRow,
    assign_splits,
    read_labels,
    shuffled,
    write_key,
    write_sheet,
)


def row(index: int, split: str = "dev") -> SheetRow:
    pair = JudgePair(
        pair_id=f"pair-{index}", query="q", claim_id=f"claim-{index}", origin="retrieved"
    )
    return SheetRow(
        pair=pair,
        question=f"subject: s{index}",
        claim=f"subject: c{index}",
        asked=("subject", "measurement"),
        split=split,
    )


def test_the_sheet_shows_inputs_only_and_the_key_holds_the_pair_data(tmp_path: Path) -> None:
    rows = [row(1), row(2, "test")]
    write_sheet(rows, tmp_path / "sheet.csv")
    write_key(rows, tmp_path / "key.csv")

    sheet = (tmp_path / "sheet.csv").read_text()
    key = (tmp_path / "key.csv").read_text()

    assert sheet.splitlines()[0] == ",".join(SHEET_COLUMNS)
    assert key.splitlines()[0] == ",".join(KEY_COLUMNS)
    for hidden in ("pair-1", "claim-1", "retrieved", ",test"):
        assert hidden not in sheet
        assert hidden in key


def test_labels_are_read_through_the_key_and_each_asked_dimension_needs_a_verdict(
    tmp_path: Path,
) -> None:
    rows = [row(1), row(2)]
    write_sheet(rows, tmp_path / "sheet.csv")
    write_key(rows, tmp_path / "key.csv")
    filled = list(csv.DictReader((tmp_path / "sheet.csv").open()))
    filled[0].update(label_subject="Match", label_measurement="narrower")
    filled[1].update(label_subject="unknown", label_measurement="mismatch")
    with (tmp_path / "sheet.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        writer.writerows(filled)

    labels = read_labels(tmp_path / "sheet.csv", tmp_path / "key.csv")

    assert labels == {
        "pair-1": {"subject": "match", "measurement": "narrower"},
        "pair-2": {"subject": "unknown", "measurement": "mismatch"},
    }


def test_a_missing_or_unasked_label_is_an_error(tmp_path: Path) -> None:
    rows = [row(1)]
    write_sheet(rows, tmp_path / "sheet.csv")
    write_key(rows, tmp_path / "key.csv")

    with pytest.raises(ValueError, match="needs a verdict"):
        read_labels(tmp_path / "sheet.csv", tmp_path / "key.csv")

    filled = list(csv.DictReader((tmp_path / "sheet.csv").open()))
    filled[0].update(label_subject="match", label_measurement="match", label_comparator="match")
    with (tmp_path / "sheet.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        writer.writerows(filled)

    with pytest.raises(ValueError, match="comparator was not asked"):
        read_labels(tmp_path / "sheet.csv", tmp_path / "key.csv")


def test_splits_follow_the_claim_work_and_do_not_move() -> None:
    pairs = [
        JudgePair(pair_id=f"p{i}", query="q", claim_id=f"c{i}", origin="reverse") for i in range(6)
    ]
    works = {f"c{i}": f"work-{i % 3}" for i in range(6)}

    first = assign_splits(pairs, works)

    assert first == assign_splits(pairs, works)
    assert first["p0"] == first["p3"]
    assert first["p1"] == first["p4"]
    assert set(first.values()) <= {"dev", "test"}


def test_shuffling_is_seeded() -> None:
    rows = [row(i) for i in range(10)]

    assert shuffled(rows, "seed") == shuffled(rows, "seed")
    assert shuffled(rows, "seed") != rows
