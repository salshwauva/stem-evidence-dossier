"""Judgment records: what a model says about one claim against one proposition.

The judge reads three meaning based dimensions: subject, comparator and
measurement. Each gets a verdict, a quote from the inputs and a one sentence
reason. Only MATCH counts as matched. The other verdicts keep the reason for the
miss visible without changing the stance rules downstream.
"""

from enum import StrEnum

from pydantic import Field, model_validator

from evidence_dossier.model import FrozenModel

SCHEMA_VERSION = "judge-v1"
REASON_LIMIT = 240
QUOTE_LIMIT = 200


class Verdict(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    # Measurement only. Each counts as not matched.
    INVERSE = "inverse"
    BROADER = "broader"
    NARROWER = "narrower"


MEASUREMENT_ONLY = frozenset({Verdict.INVERSE, Verdict.BROADER, Verdict.NARROWER})


class DimensionJudgment(FrozenModel):
    """One verdict with the words of the inputs that support it."""

    verdict: Verdict
    quote: str | None = Field(default=None, max_length=QUOTE_LIMIT)
    reason: str = Field(min_length=1, max_length=REASON_LIMIT)


class ClaimJudgment(FrozenModel):
    """The verdicts for one claim. A dimension that was not asked stays None."""

    claim_id: str
    subject: DimensionJudgment | None = None
    comparator: DimensionJudgment | None = None
    measurement: DimensionJudgment | None = None

    @model_validator(mode="after")
    def _measurement_only_verdicts(self) -> "ClaimJudgment":
        for name in ("subject", "comparator"):
            judgment: DimensionJudgment | None = getattr(self, name)
            if judgment is not None and judgment.verdict in MEASUREMENT_ONLY:
                raise ValueError(f"{name} cannot take the verdict {judgment.verdict}")
        return self


class JudgeReply(FrozenModel):
    """The JSON object a reply must be: a schema version and one judgment per claim."""

    schema_version: str
    judgments: tuple[ClaimJudgment, ...]

    @model_validator(mode="after")
    def _version(self) -> "JudgeReply":
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return self
