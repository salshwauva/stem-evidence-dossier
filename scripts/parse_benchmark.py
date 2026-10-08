"""Score the model query parser against the labeled propositions, offline by default.

    .venv/bin/python scripts/parse_benchmark.py --folder parse-bench --arm sonnet=claude-sonnet-5-5
    .venv/bin/python scripts/parse_benchmark.py --folder parse-bench --arm sonnet=claude-sonnet-5-5 \
        --queries tests/fixtures/judge/queries.json --run

The labels are the 30 propositions of tests/query_parse_benchmark.py, which one author
wrote together with the rules, so the rules arm has an edge on them. The queries of
the judge benchmark have no parse labels. They print side by side for a reader.

Each arm replays its parses from FOLDER/NAME, so a finished arm needs no model and no
network. A missing parse stops the run unless --run is given. With --run, the script
prints how many calls are missing and waits for --yes.

A text field counts as correct when it equals the label after lowercase, a dropped leading
article and collapsed spaces. The relationship is scored as the expected direction it implies:
the label names a verb family ("reduces"), and a model may write the verb it read ("cut"), so
the direction is the fair thing to compare. A negated or unknown family implies no direction.
Both arms are scored that way.
"""

import argparse
import json
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evidence_dossier.extract import ClaudeCliProvider  # noqa: E402
from evidence_dossier.model import QueryProposition, ResultDirection  # noqa: E402
from evidence_dossier.query import ModelQueryParser, QueryParseError, parse_query  # noqa: E402
from evidence_dossier.query.model_parser import build_prompt  # noqa: E402
from tests.query_parse_benchmark import CASES, ParseCase  # noqa: E402

type Parse = Callable[[str], dict[str, str | None]]

_ARTICLE = re.compile(r"^(?:the|a|an)\s+")

# The direction each relationship family of the labels implies. A negated family
# ("does not reduce") and "unknown" imply none.
_FAMILY_DIRECTION: dict[str, ResultDirection] = {
    "increases": ResultDirection.INCREASED,
    "reduces": ResultDirection.DECREASED,
    "improves": ResultDirection.IMPROVED,
    "worsens": ResultDirection.WORSENED,
    "outperforms": ResultDirection.IMPROVED,
    "underperforms": ResultDirection.WORSENED,
    "no change": ResultDirection.UNCHANGED,
}
SCORED = ("subject", "direction", "measurement", "comparator")


def norm(value: str | None) -> str | None:
    if value is None:
        return None
    return _ARTICLE.sub("", re.sub(r"\s+", " ", value.strip().lower()))


def label_of(case: ParseCase, name: str) -> str | None:
    if name == "direction":
        direction = _FAMILY_DIRECTION.get(case.relationship)
        return None if direction is None else direction.value
    return case.label_of(name)


def correct_fields(case: ParseCase, parsed: dict[str, str | None]) -> tuple[str, ...]:
    return tuple(f for f in SCORED if norm(parsed[f]) == norm(label_of(case, f)))


def verdict(case: ParseCase, correct: Sequence[str]) -> str:
    if len(correct) == len(SCORED):
        return "resolved"
    labeled = [f for f in SCORED if label_of(case, f) is not None]
    return "partial" if any(f in correct for f in labeled) else "unresolved"


def fields_of(p: QueryProposition) -> dict[str, str | None]:
    return {
        "subject": p.subject,
        "direction": None if p.expected_direction is None else p.expected_direction.value,
        "relationship": p.relationship,
        "measurement": p.measurement,
        "comparator": p.comparator,
    }


def rules_parse(case: ParseCase) -> dict[str, str | None]:
    return fields_of(parse_query(case.text, domain=case.domain))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--folder", required=True, type=Path)
    parser.add_argument("--arm", action="append", default=[], metavar="NAME=MODEL")
    parser.add_argument("--queries", type=Path, help="queries.json of the judge benchmark")
    parser.add_argument("--run", action="store_true", help="make live calls for missing parses")
    parser.add_argument("--yes", action="store_true", help="confirm the calls that --run lists")
    args = parser.parse_args()

    texts = [case.text for case in CASES]
    queries = json.loads(args.queries.read_text()) if args.queries else []
    texts += [q["text"] for q in queries]
    arms = [spec.split("=", 1) for spec in args.arm]

    parsers: dict[str, ModelQueryParser] = {}
    for name, model in arms:
        live = args.run and args.yes
        parsers[name] = ModelQueryParser(
            _live(model) if live else None,
            model_id=f"claude-cli/{model}",
            cache=args.folder / name,
        )

    if args.run and not args.yes:
        for name in parsers:
            missing = [t for t in texts if not parsers[name].is_recorded(t)]
            size = sum(len(build_prompt(t)) for t in missing) // 4
            print(f"{name}: {len(missing)} calls missing, about {size} input tokens")
        print("Add --yes to make the calls.")
        return 0

    results: dict[str, list[tuple[ParseCase, dict[str, str | None]]]] = {"rules": []}
    for name in parsers:
        results[name] = []
    try:
        for case in CASES:
            results["rules"].append((case, rules_parse(case)))
            for name, model_parser in parsers.items():
                p = model_parser.parse(case.text, domain=case.domain)
                results[name].append((case, fields_of(p)))
    except QueryParseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"{len(CASES)} labeled propositions (one author wrote the rules and the labels)\n")
    for name, rows in results.items():
        tally = {"resolved": 0, "partial": 0, "unresolved": 0}
        per_field = dict.fromkeys(SCORED, 0)
        for case, parsed in rows:
            right = correct_fields(case, parsed)
            tally[verdict(case, right)] += 1
            for f in right:
                per_field[f] += 1
        fields = "  ".join(f"{f} {per_field[f]}/{len(rows)}" for f in SCORED)
        print(
            f"{name:<10} resolved {tally['resolved']}  partial {tally['partial']}"
            f"  unresolved {tally['unresolved']}   {fields}"
        )

    for name in parsers:
        print(f"\ncases where {name} differs from the rules:")
        for (case, rule), (_, model) in zip(results["rules"], results[name], strict=True):
            if correct_fields(case, rule) != correct_fields(case, model):
                print(f"  {case.text}")
                for f in SCORED:
                    if norm(rule[f]) != norm(model[f]):
                        print(
                            f"    {f}: label {label_of(case, f)!r} | rules {rule[f]!r}"
                            f" | {name} {model[f]!r}"
                        )

    if queries:
        for name, model_parser in parsers.items():
            print(f"\n{name} on the judge benchmark queries (no labels):")
            for q in queries:
                p = model_parser.parse(q["text"])
                print(f"  {q['id']}: {q['text']}")
                print(
                    f"    subject {p.subject!r} | {p.relationship!r} | measurement {p.measurement!r}"
                    f" | comparator {p.comparator!r} | direction {p.expected_direction}"
                )
                print(f"    search terms {list(p.search_terms)}")
    return 0


def _live(model: str) -> Callable[[str], str]:
    provider = ClaudeCliProvider(model)
    return lambda prompt: provider.complete(prompt).text


if __name__ == "__main__":
    sys.exit(main())
