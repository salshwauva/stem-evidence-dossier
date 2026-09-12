"""Predicted records for the evaluate tests, derived from the dev fixture with known errors.

Every deviation from the gold is listed here once, so the hand computed
expected values in the tests and the golden report share one source.
"""

from pathlib import Path
from typing import Any

from evidence_dossier.evaluate import Dataset, GoldClaim, StancePrediction, load_dataset
from evidence_dossier.model import (
    ComparabilityLevel,
    EvidenceClaim,
    EvidenceSpan,
    ResultDirection,
    Stance,
    Term,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "evaluate"

STUDY_MAP = {
    "bio1-cells": "s-bio1-cells",
    "bio1-larvae": "s-bio1-larvae",
    "bio2-flies": "s-bio2",
    "cs1-ledger": "s-cs1",
    "cs2-corvid": "s-cs2",
}

B1, B2, C1, C2 = "work_bio_0001", "work_bio_0002", "work_cs_0001", "work_cs_0002"


def fixture_dataset() -> Dataset:
    return load_dataset(FIXTURE_DIR, "dev")


def predicted_from(gold: GoldClaim, claim_id: str, study_id: str, **changes: Any) -> EvidenceClaim:
    """Turn a gold claim into a predicted claim, with the given field changes."""
    values = gold.model_dump(exclude={"gold_key", "study_key"})
    values.update(id=claim_id, study_id=study_id, **changes)
    return EvidenceClaim.model_validate(values)


def fixture_predictions(dataset: Dataset) -> list[EvidenceClaim]:
    """Six predictions against the seven gold claims.

    - P1, P5: exact copies of bio1 c1 and cs1 c1.
    - P2: bio1 c2 with the span start moved 5 characters right (Jaccard 33/38), the
      direction DECREASED and the wrong study.
    - P4: bio2 c1 without a subject canonical form, and a method canonical form that
      differs only in case and whitespace.
    - P6: cs1 c2 with the measurement canonical form "latency per query".
    - P7: cs2 c1 in another section, so it matches nothing.
    - bio1 c3 has no prediction.
    """
    gold = {c.claim_key: c for c in dataset.claims}
    g2 = gold[f"{B1}:c2"]
    g4 = gold[f"{B2}:c1"]
    g6 = gold[f"{C1}:c2"]
    g7 = gold[f"{C2}:c1"]
    return [
        predicted_from(gold[f"{B1}:c1"], "p1", "s-bio1-cells"),
        predicted_from(
            g2,
            "p2",
            "s-bio1-cells",
            evidence_span=g2.evidence_span.model_copy(
                update={
                    "start_offset": g2.evidence_span.start_offset + 5,
                    "source_text": g2.evidence_span.source_text[5:],
                }
            ),
            result=g2.result.model_copy(update={"direction": ResultDirection.DECREASED}),
        ),
        predicted_from(
            g4,
            "p4",
            "s-bio2",
            subject=Term(original=g4.subject.original),
            method=g4.method.model_copy(
                update={"name": Term(original="knockout", canonical=" Gene Knockout ")}
            )
            if g4.method is not None
            else None,
        ),
        predicted_from(gold[f"{C1}:c1"], "p5", "s-cs1"),
        predicted_from(
            g6,
            "p6",
            "s-cs1",
            measurement=g6.measurement.model_copy(
                update={"name": Term(original="Latency per query", canonical="latency per query")}
            )
            if g6.measurement is not None
            else None,
        ),
        predicted_from(
            g7,
            "p7",
            "s-cs2",
            evidence_span=EvidenceSpan(
                research_work_id=C2,
                section_id=f"{C2}_v1_s1",
                start_offset=0,
                end_offset=46,
                source_text=g7.evidence_span.source_text,
            ),
        ),
    ]


RANKINGS: dict[str, list[str]] = {
    "q1": [f"{B1}:c1", f"{B2}:c1", "x1", "x2", "x3", f"{B1}:c2", f"{B1}:c3"],
    "q2": [f"{C1}:c2", f"{C1}:c1"],
}


def _stance(
    query_id: str, claim_id: str, stance: Stance, level: ComparabilityLevel, reason: str = ""
) -> StancePrediction:
    return StancePrediction(
        query_id=query_id, claim_id=claim_id, stance=stance, comparability=level, reason=reason
    )


# Eight of the nine gold pairs, the pair q3 with cs1 c1 left out, and one pair without a label.
STANCE_PREDICTIONS = [
    _stance("q1", f"{B1}:c1", Stance.SUPPORTS, ComparabilityLevel.HIGH),
    _stance("q1", f"{B1}:c2", Stance.NULL, ComparabilityLevel.MODERATE),
    _stance("q1", f"{B1}:c3", Stance.SUPPORTS, ComparabilityLevel.LOW),
    _stance(
        "q1",
        f"{B2}:c1",
        Stance.INDIRECT,
        ComparabilityLevel.LOW,
        "both works test a genetic or chemical change in a whole organism",
    ),
    _stance("q2", f"{C1}:c1", Stance.SUPPORTS, ComparabilityLevel.EXACT),
    _stance("q2", f"{C1}:c2", Stance.INDIRECT, ComparabilityLevel.LOW),
    _stance("q2", f"{C2}:c1", Stance.INSUFFICIENTLY_COMPARABLE, ComparabilityLevel.INCOMPATIBLE),
    _stance("q3", f"{C2}:c1", Stance.NULL, ComparabilityLevel.MODERATE),
    _stance("q3", f"{B1}:c1", Stance.INDIRECT, ComparabilityLevel.LOW),
]
