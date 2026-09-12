"""The evaluation report: every score with the model and prompt that produced it (plan section 50).

to_markdown renders plain tables in a fixed order, so two runs on the same
input give the same text. A score with an empty denominator prints as "not
assessable".
"""

from collections.abc import Iterable
from datetime import datetime

from evidence_dossier.evaluate.extraction import ExtractionEvaluation, FieldScores
from evidence_dossier.evaluate.gold import Split
from evidence_dossier.evaluate.retrieval import RetrievalEvaluation
from evidence_dossier.evaluate.scores import PRF
from evidence_dossier.evaluate.stance import StanceEvaluation
from evidence_dossier.model import FrozenModel

NOT_ASSESSABLE = "not assessable"


def fmt(value: float | None) -> str:
    return NOT_ASSESSABLE if value is None else f"{value:.3f}"


def _table(header: Iterable[str], rows: Iterable[Iterable[str]]) -> list[str]:
    head = list(header)
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _prf_rows(scores: dict[str, PRF]) -> list[list[str]]:
    return [
        [name, fmt(s.precision), fmt(s.recall), fmt(s.f1), str(s.support)]
        for name, s in scores.items()
    ]


def _field_table(scores: FieldScores) -> list[str]:
    rows = _prf_rows(scores.per_field)
    rows.extend(_prf_rows({"micro": scores.micro, "macro": scores.macro}))
    return _table(("field", "precision", "recall", "f1", "support"), rows)


class EvaluationReport(FrozenModel):
    """Scores of one configuration on one split. A section that did not run is None."""

    model_identifier: str
    prompt_version: str
    schema_version: str
    split: Split
    created_at: datetime
    extraction: ExtractionEvaluation | None = None
    retrieval: RetrievalEvaluation | None = None
    stance: StanceEvaluation | None = None
    # Where the predictions and the gold labels came from. A reader sees the
    # scores here, so the provenance of the inputs belongs here too.
    notes: tuple[str, ...] = ()

    def to_markdown(self) -> str:
        lines = [
            "# Evaluation report",
            "",
            f"- Model: {self.model_identifier}",
            f"- Prompt version: {self.prompt_version}",
            f"- Schema version: {self.schema_version}",
            f"- Split: {self.split}",
            f"- Created at: {self.created_at.isoformat()}",
            *(f"- Note: {note}" for note in self.notes),
            "",
        ]
        lines.extend(self._extraction_lines())
        lines.extend(self._retrieval_lines())
        lines.extend(self._stance_lines())
        return "\n".join(lines).rstrip() + "\n"

    def _extraction_lines(self) -> list[str]:
        e = self.extraction
        lines = ["## Extraction", ""]
        if e is None:
            return [*lines, "Not run.", ""]
        lines.extend(_field_table(e.fields))
        for title, groups in (("domain", e.by_domain), ("source level", e.by_source_level)):
            for name, scores in groups.items():
                lines.extend(["", f"### By {title}: {name}", "", *_field_table(scores)])
        lines.extend(["", "### Claim matching", ""])
        lines.append(f"- Unmatched gold claims: {_listed(e.unmatched_gold)}")
        lines.append(f"- Unmatched predicted claims: {_listed(e.unmatched_predicted)}")
        lines.extend(["", "### Field errors", ""])
        lines.extend(
            _table(
                ("gold", "predicted", "field", "gold value", "predicted value"),
                (
                    [
                        x.gold_key,
                        x.predicted_id,
                        x.field,
                        _cell(x.gold_value),
                        _cell(x.predicted_value),
                    ]
                    for x in e.field_errors
                ),
            )
        )
        r = e.relationships
        lines.extend(["", "### Relationships", ""])
        lines.append(f"- Matched claims: {r.matched}")
        lines.append(f"- Correct relationships: {r.correct}")
        lines.append(f"- Rate: {fmt(r.rate)}")
        lines.append("")
        lines.extend(
            _table(
                ("gold", "predicted", "reason"),
                ([x.gold_key, x.predicted_id, x.reason] for x in r.errors),
            )
        )
        s = e.spans
        lines.extend(["", "### Evidence spans", ""])
        lines.append(f"- Gold claims: {s.gold_claims}")
        lines.append(f"- Exact matches: {s.exact_matches} (rate {fmt(s.exact_rate)})")
        lines.append(f"- Overlap matches: {s.overlap_matches} (rate {fmt(s.overlap_rate)})")
        lines.append("")
        lines.extend(
            _table(
                ("gold", "predicted", "gold offsets", "predicted offsets"),
                (
                    [
                        x.gold_key,
                        x.predicted_id,
                        _offsets(x.gold_offsets),
                        _offsets(x.predicted_offsets),
                    ]
                    for x in s.mismatches
                ),
            )
        )
        return [*lines, ""]

    def _retrieval_lines(self) -> list[str]:
        r = self.retrieval
        lines = ["## Retrieval", ""]
        if r is None:
            return [*lines, "Not run.", ""]
        lines.append(f"- Recall@5: {fmt(r.recall_at_5)}")
        lines.append(f"- Recall@10: {fmt(r.recall_at_10)}")
        lines.append(f"- Precision@10: {fmt(r.precision_at_10)}")
        lines.append("")
        lines.extend(
            _table(
                ("query", "relevant", "returned", "recall@5", "recall@10", "precision@10"),
                (
                    [
                        q.query_id,
                        str(q.relevant),
                        str(q.returned),
                        fmt(q.recall_at_5),
                        fmt(q.recall_at_10),
                        fmt(q.precision_at_10),
                    ]
                    for q in r.per_query
                ),
            )
        )
        return [*lines, ""]

    def _stance_lines(self) -> list[str]:
        s = self.stance
        lines = ["## Stance", ""]
        if s is None:
            return [*lines, "Not run.", ""]
        lines.append(f"- Labeled pairs: {s.labeled}")
        lines.append(f"- Pairs without a prediction: {s.missing}")
        lines.append(f"- Predictions without a label: {s.extra}")
        lines.append(f"- Macro F1: {fmt(s.macro_f1)}")
        lines.append("")
        lines.extend(
            _table(("class", "precision", "recall", "f1", "support"), _prf_rows(s.per_class))
        )
        classes = list(s.confusion)
        lines.extend(["", "### Confusion matrix (rows gold, columns predicted)", ""])
        lines.extend(
            _table(
                ("gold", *classes),
                ([g, *(str(s.confusion[g][p]) for p in classes)] for g in classes),
            )
        )
        lines.extend(["", "## Comparability", ""])
        lines.append(f"- Accuracy: {fmt(s.comparability_accuracy)}")
        lines.append("")
        lines.extend(
            _table(
                ("query", "claim", "predicted", "reason"),
                (
                    [m.query_id, m.claim_id, m.predicted.value, m.reason]
                    for m in s.comparability_misses
                ),
            )
        )
        return [*lines, ""]


def _listed(items: Iterable[str]) -> str:
    listed = list(items)
    return "none" if not listed else ", ".join(listed)


def _cell(value: str | None) -> str:
    return "(absent)" if value is None else value.replace("|", "\\|")


def _offsets(pair: tuple[int, int]) -> str:
    return f"{pair[0]} to {pair[1]}"
