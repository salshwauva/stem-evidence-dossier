from enum import StrEnum

import pytest

from evidence_dossier.model import (
    ClaimType,
    ComparabilityLevel,
    Domain,
    ResultDirection,
    SectionType,
    SourceLevel,
    Stance,
    WorkLinkRelation,
)

# The expected values are copied from docs/design/implementation-plan.md and the task spec.
PLAN_VALUES: list[tuple[type[StrEnum], list[str]]] = [
    (
        Domain,
        [
            "BIOLOGY",
            "CHEMISTRY",
            "PHYSICS",
            "COMPUTER_SCIENCE",
            "ENGINEERING",
            "MATHEMATICS",
            "MULTIDISCIPLINARY",
            "OTHER_STEM",
        ],
    ),
    (SourceLevel, ["FULL_TEXT", "ABSTRACT_ONLY", "METADATA_ONLY"]),
    (
        SectionType,
        [
            "ABSTRACT",
            "INTRODUCTION",
            "BACKGROUND",
            "METHODS",
            "EXPERIMENT",
            "RESULTS",
            "EVALUATION",
            "DISCUSSION",
            "CONCLUSION",
            "APPENDIX",
            "FIGURE_CAPTION",
            "TABLE",
            "OTHER",
        ],
    ),
    (
        ClaimType,
        [
            "PERFORMANCE",
            "EFFECT",
            "ASSOCIATION",
            "COMPARISON",
            "EXISTENCE",
            "NON_EXISTENCE",
            "MECHANISM",
            "PROPERTY",
            "SCALING",
            "ROBUSTNESS",
            "REPRODUCTION",
            "THEORETICAL",
            "OTHER",
        ],
    ),
    (
        ResultDirection,
        [
            "INCREASED",
            "DECREASED",
            "IMPROVED",
            "WORSENED",
            "UNCHANGED",
            "MIXED",
            "OBSERVED",
            "NOT_OBSERVED",
            "UNKNOWN",
        ],
    ),
    (
        Stance,
        ["SUPPORTS", "CONTRADICTS", "NULL", "MIXED", "INDIRECT", "INSUFFICIENTLY_COMPARABLE"],
    ),
    (ComparabilityLevel, ["EXACT", "HIGH", "MODERATE", "LOW", "INCOMPATIBLE"]),
    (WorkLinkRelation, ["PREPRINT_OF", "VERSION_OF", "DUPLICATE_OF"]),
]


@pytest.mark.parametrize(
    ("enum", "values"), PLAN_VALUES, ids=[enum.__name__ for enum, _ in PLAN_VALUES]
)
def test_enum_values_match_the_plan(enum: type[StrEnum], values: list[str]) -> None:
    assert [member.value for member in enum] == values
