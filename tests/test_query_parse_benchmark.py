"""Checks on the hand written parse benchmark (ADR 0012).

The counts here are the numbers the README quotes. A rule change moves them,
and a reviewer sees the move in the diff.
"""

from collections import Counter

import pytest

from evidence_dossier.model import Domain
from tests.query_parse_benchmark import CASES, counts, main, run

PHYSICAL = (Domain.CHEMISTRY, Domain.PHYSICS, Domain.ENGINEERING)
VERDICTS = ("resolved", "partial", "unresolved")


def _printed_counts(text: str) -> dict[str, int]:
    tally: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in VERDICTS:
            tally[parts[0]] = int(parts[1])
    return tally


def test_the_benchmark_holds_thirty_propositions_across_the_domain_groups() -> None:
    by_domain = Counter(case.domain for case in CASES)

    assert len(CASES) == 30
    assert len({case.text for case in CASES}) == 30
    assert by_domain[Domain.COMPUTER_SCIENCE] == 10
    assert by_domain[Domain.BIOLOGY] == 10
    assert sum(by_domain[domain] for domain in PHYSICAL) == 10


def test_the_rules_resolve_twenty_of_the_thirty_propositions() -> None:
    tally = counts(run())

    assert tally == {"resolved": 20, "partial": 6, "unresolved": 4}
    assert sum(tally.values()) == len(CASES)


def test_the_script_prints_the_counts_and_the_cases_it_does_not_resolve(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main()

    printed = capsys.readouterr().out
    assert _printed_counts(printed) == counts(run())
    assert printed.count("[unresolved]") == 4
    assert printed.count("[partial]") == 6
