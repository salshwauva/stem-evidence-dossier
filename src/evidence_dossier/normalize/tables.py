"""Normalization tables (plan section 33). A new rule is a table row.

A name key is the output of fold_key: casefolded, with whitespace, hyphens
and underscores removed. A unit key is the same. The value is the canonical
form. The name tables are per domain, so "tau" maps to MAPT in biology only.
"""

from evidence_dossier.model import Domain

NAME_SYNONYMS: dict[Domain, dict[str, str]] = {
    Domain.COMPUTER_SCIENCE: {
        "resnet50": "ResNet-50",
        "a100": "NVIDIA A100",
        "a100gpu": "NVIDIA A100",
        "nvidiaa100": "NVIDIA A100",
        "nvidiaa100gpu": "NVIDIA A100",
    },
    Domain.BIOLOGY: {
        "tau": "MAPT",
        "mapt": "MAPT",
        "microtubuleassociatedproteintau": "MAPT",
    },
    Domain.CHEMISTRY: {
        "dcm": "dichloromethane",
        "dichloromethane": "dichloromethane",
        "methylenechloride": "dichloromethane",
        "thf": "tetrahydrofuran",
        "tetrahydrofuran": "tetrahydrofuran",
    },
}

# "µ" is the micro sign. Its casefold is the Greek mu "μ", so the
# keys use the mu and the canonical value keeps the micro sign.
UNIT_SYNONYMS: dict[str, str] = {
    "s": "s",
    "sec": "s",
    "second": "s",
    "seconds": "s",
    "ms": "ms",
    "millisecond": "ms",
    "milliseconds": "ms",
    "%": "%",
    "percent": "%",
    "pct": "%",
    "um": "µM",
    "μm": "µM",
    "micromolar": "µM",
}
