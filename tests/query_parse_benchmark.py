"""A hand written benchmark for the deterministic query parser (plan section 36, ADR 0012).

Every proposition below is hand written, in the words a researcher types into
a search box. Every label is hand written as well, from a plain reading of the
English, before any parser ran on the text. No model wrote a proposition, a
label or a score.

Twenty of the thirty use the subject, verb, measurement and comparator shape
that the README documents. Ten use other phrasings that researchers type: a
question about an effect, a passive question, a noun phrase, a hedge, an
association, and a verb outside the table such as "extends" or "suppresses".
One person chose that mix by hand, so it is a judgment about what people type
and not a sample of real traffic.

The label holds the four fields a correct parse yields:

- subject: what the proposition acts on, without a leading article.
- relationship: the label of the verb family when the sentence uses a verb the
  parser table names, and otherwise the relationship the sentence states in its
  own words. The families are increases, reduces, improves, worsens, no change,
  outperforms and underperforms, with "does not ..." for a negated verb. The
  label is "unknown" when the sentence states no relationship at all, such as a
  question that asks what the effect is.
- measurement: what the proposition measures, without the setting around it.
- comparator: what the proposition compares against, in the words that follow
  the comparator marker, or None when the sentence names none.

A field counts as correct when the parse equals the label exactly. Two None
values count as correct. A case is resolved when all four fields are correct,
unresolved when no field that carries a label is correct, and partial in
between.

Run it:

    .venv/bin/python -m tests.query_parse_benchmark
"""

from collections.abc import Sequence
from dataclasses import dataclass

from evidence_dossier.model import Domain
from evidence_dossier.query.parser import parse_query

FIELDS: tuple[str, ...] = ("subject", "relationship", "measurement", "comparator")


@dataclass(frozen=True)
class ParseCase:
    """One hand written proposition with the fields a correct parse yields."""

    text: str
    domain: Domain
    subject: str
    relationship: str
    measurement: str | None
    comparator: str | None

    def label_of(self, field: str) -> str | None:
        value: str | None = getattr(self, field)
        return value


CASES: tuple[ParseCase, ...] = (
    ParseCase(
        "Does retrieval-augmented generation reduce factual hallucination"
        " compared with the same model without retrieval?",
        Domain.COMPUTER_SCIENCE,
        "retrieval-augmented generation",
        "reduces",
        "factual hallucination",
        "the same model without retrieval",
    ),
    ParseCase(
        "Prompt caching cut median latency by 41% against uncached requests.",
        Domain.COMPUTER_SCIENCE,
        "prompt caching",
        "reduces",
        "median latency",
        "uncached requests",
    ),
    ParseCase(
        "Do sparse mixture-of-experts models outperform dense models on downstream accuracy?",
        Domain.COMPUTER_SCIENCE,
        "sparse mixture-of-experts models",
        "outperforms",
        "downstream accuracy",
        "dense models",
    ),
    ParseCase(
        "Quantization to 4 bits does not reduce accuracy on reasoning benchmarks.",
        Domain.COMPUTER_SCIENCE,
        "quantization to 4 bits",
        "does not reduce",
        "accuracy",
        None,
    ),
    ParseCase(
        "What is the effect of chain-of-thought prompting on arithmetic accuracy?",
        Domain.COMPUTER_SCIENCE,
        "chain-of-thought prompting",
        "unknown",
        "arithmetic accuracy",
        None,
    ),
    ParseCase(
        "Speculative decoding boosts tokens per second versus greedy decoding.",
        Domain.COMPUTER_SCIENCE,
        "speculative decoding",
        "increases",
        "tokens per second",
        "greedy decoding",
    ),
    ParseCase(
        "Is data augmentation associated with generalization gains in small image datasets?",
        Domain.COMPUTER_SCIENCE,
        "data augmentation",
        "is associated with",
        "generalization gains",
        None,
    ),
    ParseCase(
        "Is the defect rate lowered by static type checking in large codebases?",
        Domain.COMPUTER_SCIENCE,
        "static type checking",
        "reduces",
        "defect rate",
        None,
    ),
    ParseCase(
        "Does gradient checkpointing degrade training throughput"
        " compared to full activation storage?",
        Domain.COMPUTER_SCIENCE,
        "gradient checkpointing",
        "worsens",
        "training throughput",
        "full activation storage",
    ),
    ParseCase(
        "Longer context windows have no effect on answer quality over 4k token contexts.",
        Domain.COMPUTER_SCIENCE,
        "longer context windows",
        "no change",
        "answer quality",
        "4k token contexts",
    ),
    ParseCase(
        "MAPT knockdown increases neuronal survival compared with a scrambled control.",
        Domain.BIOLOGY,
        "mapt knockdown",
        "increases",
        "neuronal survival",
        "a scrambled control",
    ),
    ParseCase(
        "Does metformin lower fasting glucose in type 2 diabetes compared with placebo?",
        Domain.BIOLOGY,
        "metformin",
        "reduces",
        "fasting glucose",
        "placebo",
    ),
    ParseCase(
        "SIRT1 overexpression does not change mitochondrial density in muscle fibres.",
        Domain.BIOLOGY,
        "sirt1 overexpression",
        "no change",
        "mitochondrial density",
        None,
    ),
    ParseCase(
        "Chronic sleep restriction worsens memory consolidation"
        " relative to an eight hour schedule.",
        Domain.BIOLOGY,
        "chronic sleep restriction",
        "worsens",
        "memory consolidation",
        "an eight hour schedule",
    ),
    ParseCase(
        "Faecal microbiota transplantation improves insulin sensitivity in mice"
        " versus sham treatment.",
        Domain.BIOLOGY,
        "faecal microbiota transplantation",
        "improves",
        "insulin sensitivity",
        "sham treatment",
    ),
    ParseCase(
        "Is there evidence that CRISPR base editing reduces off-target mutations?",
        Domain.BIOLOGY,
        "crispr base editing",
        "reduces",
        "off-target mutations",
        None,
    ),
    ParseCase(
        "Whether exercise raises BDNF levels in older adults",
        Domain.BIOLOGY,
        "exercise",
        "increases",
        "bdnf levels",
        None,
    ),
    ParseCase(
        "How does high salt intake affect endothelial function?",
        Domain.BIOLOGY,
        "high salt intake",
        "unknown",
        "endothelial function",
        None,
    ),
    ParseCase(
        "Does vitamin D supplementation have no effect on fracture risk?",
        Domain.BIOLOGY,
        "vitamin d supplementation",
        "no change",
        "fracture risk",
        None,
    ),
    ParseCase(
        "Rapamycin extends median lifespan in mice relative to untreated controls.",
        Domain.BIOLOGY,
        "rapamycin",
        "increases",
        "median lifespan",
        "untreated controls",
    ),
    ParseCase(
        "Graphene doping lowers the sheet resistance relative to pristine films.",
        Domain.PHYSICS,
        "graphene doping",
        "reduces",
        "sheet resistance",
        "pristine films",
    ),
    ParseCase(
        "The palladium catalyst raises the isolated yield versus the uncatalysed route.",
        Domain.CHEMISTRY,
        "palladium catalyst",
        "increases",
        "isolated yield",
        "the uncatalysed route",
    ),
    ParseCase(
        "Does annealing at 600 C improve the tensile strength of the alloy?",
        Domain.ENGINEERING,
        "annealing at 600 c",
        "improves",
        "tensile strength of the alloy",
        None,
    ),
    ParseCase(
        "Effect of fly ash on the 28 day compressive strength of concrete"
        " compared with ordinary Portland cement",
        Domain.ENGINEERING,
        "fly ash",
        "unknown",
        "28 day compressive strength of concrete",
        "ordinary portland cement",
    ),
    ParseCase(
        "Perovskite tandem cells outperform silicon cells on power conversion efficiency.",
        Domain.PHYSICS,
        "perovskite tandem cells",
        "outperforms",
        "power conversion efficiency",
        "silicon cells",
    ),
    ParseCase(
        "Do lithium iron phosphate cells underperform NMC cells on energy density?",
        Domain.ENGINEERING,
        "lithium iron phosphate cells",
        "underperforms",
        "energy density",
        "nmc cells",
    ),
    ParseCase(
        "Hydrogen embrittlement may degrade fatigue life in pipeline steel.",
        Domain.ENGINEERING,
        "hydrogen embrittlement",
        "worsens",
        "fatigue life",
        None,
    ),
    ParseCase(
        "Ultrasonic welding does not lower the joint strength of aluminium sheets.",
        Domain.ENGINEERING,
        "ultrasonic welding",
        "does not reduce",
        "joint strength of aluminium sheets",
        None,
    ),
    ParseCase(
        "Do shielded qubits show a longer decoherence time than unshielded qubits?",
        Domain.PHYSICS,
        "shielded qubits",
        "increases",
        "decoherence time",
        "unshielded qubits",
    ),
    ParseCase(
        "Does a zeolite catalyst suppress coke formation compared with the amorphous support?",
        Domain.CHEMISTRY,
        "zeolite catalyst",
        "reduces",
        "coke formation",
        "the amorphous support",
    ),
)


@dataclass(frozen=True)
class CaseResult:
    """What the parser returned for one case, and which fields it got right."""

    case: ParseCase
    parsed: dict[str, str | None]
    correct: tuple[str, ...]

    @property
    def verdict(self) -> str:
        if len(self.correct) == len(FIELDS):
            return "resolved"
        labeled = [field for field in FIELDS if self.case.label_of(field) is not None]
        if any(field in self.correct for field in labeled):
            return "partial"
        return "unresolved"

    def misses(self) -> list[str]:
        """One line per field the parse got wrong."""
        return [
            f"{field}: label {self.case.label_of(field)!r}, parse {self.parsed[field]!r}"
            for field in FIELDS
            if field not in self.correct
        ]


def score(case: ParseCase) -> CaseResult:
    """Parse one case and compare every field against its label."""
    proposition = parse_query(case.text, domain=case.domain)
    parsed: dict[str, str | None] = {
        "subject": proposition.subject,
        "relationship": proposition.relationship,
        "measurement": proposition.measurement,
        "comparator": proposition.comparator,
    }
    correct = tuple(field for field in FIELDS if parsed[field] == case.label_of(field))
    return CaseResult(case, parsed, correct)


def run(cases: Sequence[ParseCase] = CASES) -> list[CaseResult]:
    return [score(case) for case in cases]


def counts(results: Sequence[CaseResult]) -> dict[str, int]:
    """Count the results by verdict. Every case lands in one of the three."""
    tally = {"resolved": 0, "partial": 0, "unresolved": 0}
    for result in results:
        tally[result.verdict] += 1
    return tally


def main() -> None:
    results = run()
    tally = counts(results)
    print(f"query parse benchmark: {len(results)} hand written propositions")
    for verdict in ("resolved", "partial", "unresolved"):
        print(f"{verdict:<11}{tally[verdict]:>3}")
    print("\ncases the rules do not resolve:")
    for result in results:
        if result.verdict == "resolved":
            continue
        print(f"  [{result.verdict}] {result.case.text}")
        for miss in result.misses():
            print(f"      {miss}")


if __name__ == "__main__":
    main()
