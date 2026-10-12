"""Draw one batch of the stop reason gold sheet from ClinicalTrials.gov.

The first run fetches every stopped cohort trial and saves it as pool.jsonl, so
every later batch draws from the same snapshot. A batch never repeats a trial
from the exclusion files or from an earlier batch.

    .venv/bin/python scripts/sample_stop_reasons.py --batch 1
    .venv/bin/python scripts/sample_stop_reasons.py --batch 2
"""

import argparse
import csv
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from evidence_dossier.evaluate import (
    COHORT_KEYWORDS,
    StoppedTrial,
    draw_batch,
    fetch_stopped_trials,
    write_key,
    write_sheet,
)
from evidence_dossier.ingest import HttpxClient, PacedHttpClient

# The registry asks for at most about 50 requests a minute from one address.
REQUEST_INTERVAL_SECONDS = 1.3


def load_pool(path: Path) -> list[StoppedTrial]:
    pool: list[StoppedTrial] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        record["phases"] = tuple(record["phases"])
        pool.append(StoppedTrial(**record))
    return pool


def save_pool(pool: list[StoppedTrial], path: Path) -> None:
    path.write_text("".join(json.dumps(asdict(trial)) + "\n" for trial in pool), encoding="utf-8")


def read_ids(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def read_key_ids(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["nct_id"] for row in csv.DictReader(handle)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--batch", type=int, required=True, help="batch number, from 1")
    parser.add_argument("--size", type=int, default=150, help="notes in the batch (default 150)")
    parser.add_argument("--seed", help="seed of the draw (default stop-reasons-batch-N)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(".claude/stop-reason-gold"),
        help="folder for the pool, sheets, keys and manifest",
    )
    parser.add_argument(
        "--exclude",
        type=Path,
        action="append",
        default=None,
        help="file of NCT IDs to keep out (default .claude/stop-reason-exploration-ids.txt)",
    )
    parser.add_argument("--refetch", action="store_true", help="fetch a new pool snapshot")
    args = parser.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    sheet_path = out / f"batch{args.batch}_sheet.csv"
    key_path = out / f"batch{args.batch}_key.csv"
    if sheet_path.exists() or key_path.exists():
        print(f"error: batch {args.batch} exists in {out}", file=sys.stderr)
        return 1

    earlier_keys = sorted(out.glob("batch*_key.csv"))
    pool_path = out / "pool.jsonl"
    manifest_path = out / "manifest.json"
    if args.refetch and earlier_keys:
        print("error: an earlier batch drew from the current pool, so it stays", file=sys.stderr)
        return 1
    if pool_path.exists() and not args.refetch:
        pool = load_pool(pool_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        client = PacedHttpClient(HttpxClient(), REQUEST_INTERVAL_SECONDS)
        pool = fetch_stopped_trials(client.get)
        save_pool(pool, pool_path)
        manifest = {
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "pool_size": len(pool),
            "pool_with_note": sum(1 for trial in pool if trial.note),
            "cohort_keywords": list(COHORT_KEYWORDS),
            "batches": [],
        }

    exclude_files: list[Path] = args.exclude or [Path(".claude/stop-reason-exploration-ids.txt")]
    excluded: set[str] = set()
    for path in exclude_files:
        excluded |= read_ids(path)
    for path in earlier_keys:
        excluded |= read_key_ids(path)

    seed = args.seed or f"stop-reasons-batch-{args.batch}"
    batch = draw_batch(pool, seed=seed, size=args.size, exclude=excluded)
    write_sheet(batch, sheet_path)
    write_key(batch, key_path)
    manifest["batches"].append(
        {"batch": args.batch, "seed": seed, "size": args.size, "excluded": len(excluded)}
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        f"pool: {manifest['pool_size']} stopped cohort trials, {manifest['pool_with_note']} with a note"
    )
    print(f"excluded: {len(excluded)}")
    print(f"batch {args.batch}: {len(batch)} notes, seed {seed}")
    print(f"sheet: {sheet_path}")
    print(f"key (do not open while labeling): {key_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
