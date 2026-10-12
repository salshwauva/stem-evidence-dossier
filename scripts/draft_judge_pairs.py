"""Draw the query and claim pairs of the judge benchmark and write the blind labeling sheet.

    .venv/bin/python scripts/draft_judge_pairs.py --db demo.db --queries queries.json --out judge-pairs

queries.json holds a list of {"id", "text", "origin"} objects. A "retrieved" query is
searched, and the draw samples its candidates. A "reverse" query also names the
"claim_id" it was written from, and gives exactly that pair. Write the queries before
looking at the claims. The script writes pairs.json (all pairs), sheet.csv (for the
annotator) and key.csv (opened after the labels are done).
"""

import argparse
import json
import random
import sys
from collections.abc import Callable
from pathlib import Path

from evidence_dossier.evaluate.judge import JudgePair
from evidence_dossier.evaluate.judge_sheet import (
    SheetRow,
    assign_splits,
    shuffled,
    write_key,
    write_sheet,
)
from evidence_dossier.extract import ClaudeCliProvider
from evidence_dossier.model import QueryProposition
from evidence_dossier.query import ModelQueryParser, QueryParseError, Retriever, parse_query
from evidence_dossier.query.model_comparator import shown_inputs
from evidence_dossier.store import Store


def _parse_function(model: str | None, folder: Path) -> Callable[[str], QueryProposition]:
    """Return the parser search uses: the rules, or the model path with its recorded parses."""
    if model is None:
        return parse_query
    provider = ClaudeCliProvider(model)
    parser = ModelQueryParser(
        lambda prompt: provider.complete(prompt).text, model_id=f"claude-cli/{model}", cache=folder
    )
    return parser.parse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--queries", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--per-query", type=int, default=4, help="candidates sampled per retrieved query"
    )
    parser.add_argument("--per-work", type=int, default=8, help="most pairs from one work")
    parser.add_argument("--seed", default="judge-pairs-1")
    parser.add_argument("--no-passage", action="store_true")
    parser.add_argument("--parse-model", help="read the queries with this model, as search does")
    parser.add_argument("--parses", type=Path, default=Path("parses"))
    args = parser.parse_args()
    queries = json.loads(args.queries.read_text(encoding="utf-8"))
    parse = _parse_function(args.parse_model, args.parses)
    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    pairs: list[JudgePair] = []
    works: dict[str, str] = {}
    per_work: dict[str, int] = {}
    with Store(args.db) as store:
        for query in queries:
            proposition = parse(query["text"])
            if query["origin"] == "reverse":
                claim_ids = [query["claim_id"]]
            else:
                found = Retriever(store).retrieve(proposition, limit=20)
                claim_ids = [c.claim.id for c in found]
                rng.shuffle(claim_ids)
            taken = 0
            for claim_id in claim_ids:
                claim = store.get_claim(claim_id)
                if claim is None:
                    raise SystemExit(f"error: no claim {claim_id} for query {query['id']}")
                work = claim.research_work_id
                if query["origin"] == "retrieved" and (
                    taken >= args.per_query or per_work.get(work, 0) >= args.per_work
                ):
                    continue
                taken += 1
                per_work[work] = per_work.get(work, 0) + 1
                works[claim_id] = work
                pairs.append(
                    JudgePair(
                        pair_id=f"{query['id']}:{claim_id}",
                        query=query["text"],
                        claim_id=claim_id,
                        origin=query["origin"],
                    )
                )
        splits = assign_splits(pairs, works)
        rows = []
        for pair in pairs:
            claim = store.get_claim(pair.claim_id)
            assert claim is not None
            question, claim_text, asked = shown_inputs(
                parse(pair.query), claim, include_passage=not args.no_passage
            )
            rows.append(SheetRow(pair, question, claim_text, asked, splits[pair.pair_id]))
    ordered = shuffled(rows, args.seed)
    (args.out / "pairs.json").write_text(
        json.dumps([p.model_dump() for p in pairs], indent=2) + "\n", encoding="utf-8"
    )
    write_sheet(ordered, args.out / "sheet.csv")
    write_key(ordered, args.out / "key.csv")
    sides = [row.split for row in rows]
    print(f"{len(rows)} pairs ({sides.count('dev')} dev, {sides.count('test')} test) in {args.out}")
    print("Label sheet.csv without opening key.csv.")
    return 0


def run() -> int:
    try:
        return main()
    except QueryParseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
