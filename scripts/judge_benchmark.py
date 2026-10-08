"""Score the comparability judge arms against the human labels, offline by default.

    .venv/bin/python scripts/judge_benchmark.py --db demo.db --pairs judge-pairs --split dev \
        --arm sonnet=claude-sonnet-5-5:1:passage

An arm is NAME=MODEL:BATCH:INPUT, with INPUT passage or fields. Each arm reads and
writes its validated judgments in PAIRS/judgments/NAME, so a finished arm replays with
no model and no network. A missing judgment stops the run unless --run is given. With
--run, the script prints the prompt count and an input size estimate first and waits
for --yes, because every missing batch is a live model call.

The rules arm (word overlap) and an arm that always answers unknown score on the same
pairs. The gate compares each model arm with the rules arm. Run the test split once,
after the prompt, the arms and the gate are frozen on the dev split.
"""

import argparse
import csv
import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path

from evidence_dossier.evaluate import Gate, JudgePair, apply_gate, score_arm
from evidence_dossier.evaluate.judge import ArmScore, Verdicts
from evidence_dossier.evaluate.judge_sheet import read_labels
from evidence_dossier.extract import ClaudeCliProvider
from evidence_dossier.model import EvidenceClaim, QueryProposition
from evidence_dossier.profiles import get_profile
from evidence_dossier.query import (
    ClaimJudgment,
    ComparabilityEngine,
    ComparatorError,
    JudgmentCache,
    ModelComparator,
    ModelQueryParser,
    parse_query,
)
from evidence_dossier.query.model_comparator import asked_dimensions, build_prompt
from evidence_dossier.store import Store

DIMENSIONS = ("subject", "comparator", "measurement")


def to_verdicts(pair: JudgePair, judgment: ClaimJudgment) -> dict[str, str]:
    return {
        name: given.verdict.value
        for name in DIMENSIONS
        if (given := getattr(judgment, name)) is not None
    }


def rules_verdicts(proposition: QueryProposition, claim: EvidenceClaim) -> dict[str, str]:
    assessment = ComparabilityEngine().assess(
        proposition, claim, get_profile(claim.research_context.domain)
    )
    asked = asked_dimensions(proposition, claim)
    return {
        result.dimension: "match" if result.matched else "mismatch"
        for result in assessment.dimensions
        if result.dimension in asked
    }


def unknown_verdicts(proposition: QueryProposition, claim: EvidenceClaim) -> dict[str, str]:
    return {name: "unknown" for name in asked_dimensions(proposition, claim)}


def format_arm(score: ArmScore) -> list[str]:
    lines = [f"{score.arm}"]
    for d in (*score.dimensions, score.total):
        if d.pairs == 0:
            continue
        interval = d.false_match_interval
        shown = "95% n/a" if interval is None else f"95% {interval[0]:.2f} to {interval[1]:.2f}"
        lines.append(
            f"  {d.dimension:<12} pairs {d.pairs:>3}  matches {d.positives:>3}"
            f"  false matches {d.false_matches:>2}/{d.negatives:<3} ({shown})"
            f"  missed {d.missed_matches:>2}  unknown {d.unknowns:>2}"
            f"  matched agreement {d.matched_agreements}/{d.pairs}"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--pairs", required=True, type=Path)
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--parse-model", help="replay the parses of this model, as the pairs used")
    parser.add_argument("--parses", type=Path, default=Path("parses"))
    parser.add_argument("--arm", action="append", default=[], metavar="NAME=MODEL:BATCH:INPUT")
    parser.add_argument(
        "--run", action="store_true", help="make live model calls for missing judgments"
    )
    parser.add_argument(
        "--yes", action="store_true", help="confirm the live calls that --run lists"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)

    pairs = [JudgePair(**p) for p in json.loads((args.pairs / "pairs.json").read_text())]
    labels = read_labels(args.pairs / "sheet.csv", args.pairs / "key.csv")
    with (args.pairs / "key.csv").open(newline="", encoding="utf-8") as handle:
        side = {row["pair_id"]: row["split"] for row in csv.DictReader(handle)}
    chosen = [p for p in pairs if side[p.pair_id] == args.split]
    ids = [p.pair_id for p in chosen]
    scores: dict[str, ArmScore] = {}
    with Store(args.db) as store:
        claims = _load_claims(store, chosen)
        parse = _replay_parser(args.parse_model, args.parses)
        propositions = {p.query: parse(p.query) for p in chosen}

        def per_pair(make: Callable[[QueryProposition, EvidenceClaim], dict[str, str]]) -> Verdicts:
            return {p.pair_id: make(propositions[p.query], claims[p.claim_id]) for p in chosen}

        scores["rules"] = score_arm("rules", labels, per_pair(rules_verdicts), ids)
        scores["unknown"] = score_arm("unknown", labels, per_pair(unknown_verdicts), ids)
        arms = [spec.split("=", 1) for spec in args.arm]
        plans = []
        for name, spec in arms:
            model, batch, source = spec.split(":")
            comparator = ModelComparator(
                _live(model) if args.run and args.yes else None,
                model_id=f"claude-cli/{model}",
                cache=JudgmentCache(args.pairs / "judgments" / name),
                batch_size=int(batch),
                include_passage=source == "passage",
            )
            plans.append((name, comparator, source == "passage", int(batch)))
        if args.run and not args.yes:
            for name, _, passage, batch in plans:
                prompts = [
                    build_prompt(
                        propositions[q],
                        [claims[p.claim_id] for p in group],
                        include_passage=passage,
                    )
                    for q in propositions
                    for group in _groups([p for p in chosen if p.query == q], batch)
                ]
                print(
                    f"{name}: {len(prompts)} prompts, about {sum(len(x) for x in prompts) // 4} input tokens (cached batches cost nothing)"
                )
            print("Add --yes to make the calls.")
            return 0
        for name, comparator, _, _ in plans:
            verdicts: dict[str, dict[str, str]] = {}
            try:
                for query, proposition in propositions.items():
                    group = [p for p in chosen if p.query == query]
                    judged = comparator.judge(proposition, [claims[p.claim_id] for p in group])
                    for p in group:
                        verdicts[p.pair_id] = to_verdicts(p, judged[p.claim_id])
            except ComparatorError as error:
                print(f"error: arm {name}: {error}", file=sys.stderr)
                return 1
            scores[name] = score_arm(name, labels, verdicts, ids)
    print(f"split {args.split}: {len(chosen)} pairs\n")
    for score in scores.values():
        print("\n".join(format_arm(score)))
        if score.arm not in ("rules", "unknown"):
            result = apply_gate(score, scores["rules"], Gate())
            print("  gate:", "pass" if result.passed else "fail: " + "; ".join(result.reasons))
        print()
    return 0


def _replay_parser(model: str | None, folder: Path) -> Callable[[str], QueryProposition]:
    """The parser the pairs were drafted with. It only replays, so the benchmark makes no parse call."""
    if model is None:
        return parse_query
    return ModelQueryParser(None, model_id=f"claude-cli/{model}", cache=folder).parse


def _live(model: str) -> Callable[[str], str]:
    provider = ClaudeCliProvider(model)
    return lambda prompt: provider.complete(prompt).text


def _load_claims(store: Store, pairs: list[JudgePair]) -> dict[str, EvidenceClaim]:
    claims: dict[str, EvidenceClaim] = {}
    for pair in pairs:
        claim = store.get_claim(pair.claim_id)
        if claim is None:
            raise SystemExit(f"error: no claim {pair.claim_id} in the store")
        claims[pair.claim_id] = claim
    return claims


def _groups(pairs: list[JudgePair], size: int) -> list[list[JudgePair]]:
    ordered = sorted(pairs, key=lambda p: p.claim_id)
    return [ordered[i : i + size] for i in range(0, len(ordered), size)]


if __name__ == "__main__":
    sys.exit(main())
