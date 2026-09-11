"""Enumerations for the core model.

Where the implementation plan lists values, the values match the plan text exactly.
"""

from enum import StrEnum


class Domain(StrEnum):
    """Research domain of a work or of a claim context (plan section 28)."""

    BIOLOGY = "BIOLOGY"
    CHEMISTRY = "CHEMISTRY"
    PHYSICS = "PHYSICS"
    COMPUTER_SCIENCE = "COMPUTER_SCIENCE"
    ENGINEERING = "ENGINEERING"
    MATHEMATICS = "MATHEMATICS"
    MULTIDISCIPLINARY = "MULTIDISCIPLINARY"
    OTHER_STEM = "OTHER_STEM"


class SourceLevel(StrEnum):
    """How much of a work the extractor could read (plan section 12)."""

    FULL_TEXT = "FULL_TEXT"
    ABSTRACT_ONLY = "ABSTRACT_ONLY"
    METADATA_ONLY = "METADATA_ONLY"


class SectionType(StrEnum):
    """Generic section types that profiles map headings onto (plan section 13)."""

    ABSTRACT = "ABSTRACT"
    INTRODUCTION = "INTRODUCTION"
    BACKGROUND = "BACKGROUND"
    METHODS = "METHODS"
    EXPERIMENT = "EXPERIMENT"
    RESULTS = "RESULTS"
    EVALUATION = "EVALUATION"
    DISCUSSION = "DISCUSSION"
    CONCLUSION = "CONCLUSION"
    APPENDIX = "APPENDIX"
    FIGURE_CAPTION = "FIGURE_CAPTION"
    TABLE = "TABLE"
    OTHER = "OTHER"


class ClaimType(StrEnum):
    """Generalized claim types (plan section 16)."""

    PERFORMANCE = "PERFORMANCE"
    EFFECT = "EFFECT"
    ASSOCIATION = "ASSOCIATION"
    COMPARISON = "COMPARISON"
    EXISTENCE = "EXISTENCE"
    NON_EXISTENCE = "NON_EXISTENCE"
    MECHANISM = "MECHANISM"
    PROPERTY = "PROPERTY"
    SCALING = "SCALING"
    ROBUSTNESS = "ROBUSTNESS"
    REPRODUCTION = "REPRODUCTION"
    THEORETICAL = "THEORETICAL"
    OTHER = "OTHER"


class ResultDirection(StrEnum):
    """Generalized result directions (plan section 21)."""

    INCREASED = "INCREASED"
    DECREASED = "DECREASED"
    IMPROVED = "IMPROVED"
    WORSENED = "WORSENED"
    UNCHANGED = "UNCHANGED"
    MIXED = "MIXED"
    OBSERVED = "OBSERVED"
    NOT_OBSERVED = "NOT_OBSERVED"
    UNKNOWN = "UNKNOWN"


class Stance(StrEnum):
    """How a claim relates to a query proposition (plan section 39)."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NULL = "NULL"
    MIXED = "MIXED"
    INDIRECT = "INDIRECT"
    INSUFFICIENTLY_COMPARABLE = "INSUFFICIENTLY_COMPARABLE"


class ComparabilityLevel(StrEnum):
    """How closely a claim matches a query proposition (plan section 37)."""

    EXACT = "EXACT"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INCOMPATIBLE = "INCOMPATIBLE"


class WorkLinkRelation(StrEnum):
    """Relation from one research work to another (plan section 46)."""

    PREPRINT_OF = "PREPRINT_OF"
    VERSION_OF = "VERSION_OF"
    DUPLICATE_OF = "DUPLICATE_OF"


class ValidationStatus(StrEnum):
    """Outcome of schema and relationship validation for one extraction run."""

    VALID = "VALID"
    INVALID = "INVALID"
