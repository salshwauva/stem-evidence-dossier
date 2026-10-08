"""The blind pair sheet for the judge benchmark (docs/judge-labeling-guidelines.md).

The sheet shows the inputs the judge receives and nothing else: no rule result, no
model verdict, no stance. A second file, the key, maps each row back to its pair,
claim, origin and split. The annotator does not open the key until every label is
written. The caller builds the rows, because this package never imports the query
package (ADR 0008).
"""

import csv
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from evidence_dossier.evaluate.judge import DIMENSIONS, VERDICTS, JudgePair, Verdicts
from evidence_dossier.evaluate.split import DatasetSplitter

SHEET_COLUMNS = (
    "row",
    "question",
    "claim",
    "asked",
    "label_subject",
    "label_comparator",
    "label_measurement",
    "unsure",
    "comment",
)
KEY_COLUMNS = ("row", "pair_id", "claim_id", "origin", "split")
SPLIT_SALT = "judge-pairs-1"


@dataclass(frozen=True)
class SheetRow:
    """One pair with the text the annotator sees and the dimensions to label."""

    pair: JudgePair
    question: str
    claim: str
    asked: tuple[str, ...]
    split: str


def assign_splits(
    pairs: Sequence[JudgePair], claim_work: Mapping[str, str], dev_ratio: float = 0.6
) -> dict[str, str]:
    """Assign each pair the side of its claim's work, so related claims stay together."""
    sides = DatasetSplitter(dev_ratio=dev_ratio, salt=SPLIT_SALT).assign(
        sorted(set(claim_work.values()))
    )
    return {pair.pair_id: sides[claim_work[pair.claim_id]] for pair in pairs}


def shuffled(rows: Sequence[SheetRow], seed: str) -> list[SheetRow]:
    """Order the rows at random, so a reader cannot follow one query down the sheet."""
    ordered = list(rows)
    random.Random(seed).shuffle(ordered)
    return ordered


def row_name(index: int) -> str:
    return f"r{index + 1:03d}"


def write_sheet(rows: Sequence[SheetRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SHEET_COLUMNS)
        for index, row in enumerate(rows):
            writer.writerow(
                [row_name(index), row.question, row.claim, ", ".join(row.asked), "", "", "", "", ""]
            )


def write_key(rows: Sequence[SheetRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(KEY_COLUMNS)
        for index, row in enumerate(rows):
            pair = row.pair
            writer.writerow([row_name(index), pair.pair_id, pair.claim_id, pair.origin, row.split])


def read_labels(sheet: Path, key: Path) -> Verdicts:
    """Return pair ID to dimension to label. Every asked dimension needs a label from the verdict set."""
    with key.open(newline="", encoding="utf-8") as handle:
        pair_of = {row["row"]: row["pair_id"] for row in csv.DictReader(handle)}
    labels: dict[str, dict[str, str]] = {}
    with sheet.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = row["row"]
            asked = [part.strip() for part in row["asked"].split(",") if part.strip()]
            given: dict[str, str] = {}
            for dimension in DIMENSIONS:
                value = row[f"label_{dimension}"].strip().lower()
                if dimension in asked and value not in VERDICTS:
                    raise ValueError(f"row {name}: {dimension} needs a verdict, got {value!r}")
                if dimension not in asked and value:
                    raise ValueError(f"row {name}: {dimension} was not asked")
                if value:
                    given[dimension] = value
            labels[pair_of[name]] = given
    return labels
