import pytest

from evidence_dossier.evaluate import Gate, apply_gate, score_arm, wilson_interval
from evidence_dossier.evaluate.judge import DimensionScore

# Invented labels and verdicts. They test the arithmetic and say nothing about any model.
LABELS = {
    "p1": {"subject": "match", "measurement": "match"},
    "p2": {"subject": "mismatch", "measurement": "mismatch"},
    "p3": {"subject": "unknown", "measurement": "narrower"},
    "p4": {"subject": "match", "measurement": "mismatch"},
}


def verdicts(**by_pair: dict[str, str]) -> dict[str, dict[str, str]]:
    return by_pair


def test_wilson_interval_matches_known_values_and_handles_the_edges() -> None:
    low, high = wilson_interval(36, 40) or (0, 0)
    assert round(low, 2) == 0.77
    assert round(high, 2) == 0.96
    zero_low, zero_high = wilson_interval(0, 30) or (1, 1)
    assert zero_low == 0.0
    assert 0.10 < zero_high < 0.12
    assert wilson_interval(0, 0) is None


def test_counts_false_matches_missed_matches_and_unknowns_per_dimension() -> None:
    arm = verdicts(
        p1={"subject": "match", "measurement": "unknown"},
        p2={"subject": "match", "measurement": "mismatch"},
        p3={"subject": "unknown", "measurement": "match"},
        p4={"subject": "mismatch", "measurement": "mismatch"},
    )

    score = score_arm("fake", LABELS, arm)
    subject, comparator, measurement = score.dimensions

    assert (subject.pairs, subject.positives) == (4, 2)
    assert subject.false_matches == 1  # p2
    assert subject.missed_matches == 1  # p4
    assert subject.unknowns == 1  # p3
    assert subject.matched_agreements == 2  # p1, p3
    assert (comparator.pairs, comparator.false_match_rate) == (0, None)
    assert measurement.false_matches == 1  # p3 is narrower in the label
    assert measurement.missed_matches == 1  # p1
    assert measurement.unknowns == 1  # p1
    assert score.total.false_matches == 2


def test_a_labeled_dimension_with_no_verdict_is_a_miss_and_never_a_gain() -> None:
    score = score_arm("silent", LABELS, {})

    subject = score.dimensions[0]
    assert subject.unanswered == 4
    assert subject.missed_matches == 2
    assert subject.false_matches == 0
    assert subject.matched_agreements == 0


def test_an_unknown_label_is_not_a_match() -> None:
    arm = verdicts(p3={"subject": "match"})

    score = score_arm("fake", LABELS, arm, pair_ids=["p3"])

    assert score.dimensions[0].false_matches == 1


def test_a_label_outside_the_verdict_set_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a verdict"):
        score_arm("fake", {"p1": {"subject": "maybe"}}, {})


def test_the_gate_blocks_an_arm_that_always_says_unknown() -> None:
    rules = score_arm(
        "rules",
        LABELS,
        verdicts(
            p1={"subject": "match", "measurement": "match"},
            p2={"subject": "mismatch", "measurement": "mismatch"},
            p3={"subject": "mismatch", "measurement": "mismatch"},
            p4={"subject": "match", "measurement": "mismatch"},
        ),
    )
    silent = score_arm(
        "unknown",
        LABELS,
        {pair: {"subject": "unknown", "measurement": "unknown"} for pair in LABELS},
    )

    result = apply_gate(silent, rules, Gate())

    assert not result.passed
    assert any("recall" in reason for reason in result.reasons)
    assert not any("false matches" in reason for reason in result.reasons)


def test_the_gate_passes_an_arm_that_finds_matches_without_extra_false_matches() -> None:
    perfect = score_arm(
        "perfect",
        LABELS,
        {
            "p1": {"subject": "match", "measurement": "match"},
            "p2": {"subject": "mismatch", "measurement": "mismatch"},
            "p3": {"subject": "unknown", "measurement": "narrower"},
            "p4": {"subject": "match", "measurement": "mismatch"},
        },
    )
    rules = score_arm(
        "rules",
        LABELS,
        {
            "p1": {"subject": "match", "measurement": "mismatch"},
            "p2": {"subject": "match", "measurement": "mismatch"},
            "p3": {"subject": "mismatch", "measurement": "mismatch"},
            "p4": {"subject": "mismatch", "measurement": "mismatch"},
        },
    )

    assert apply_gate(perfect, rules, Gate()).passed


def test_dimension_score_rates_read_none_for_empty_denominators() -> None:
    empty = DimensionScore(
        dimension="subject",
        pairs=0,
        positives=0,
        exact_agreements=0,
        matched_agreements=0,
        false_matches=0,
        missed_matches=0,
        unknowns=0,
        unanswered=0,
    )

    assert empty.false_match_rate is None
    assert empty.recall is None
    assert empty.false_match_interval is None
