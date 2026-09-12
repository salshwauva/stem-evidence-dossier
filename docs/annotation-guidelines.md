# Annotation guidelines

These rules precede the labels (plan section 49). An annotator applies them to every gold document, and the evaluate package scores against them. A rule change is a new guideline version, and labels made under an older version do not mix with newer ones in one split.

## What counts as a claim

A claim is one reported finding from one study in one research work. It names a subject, a predicate and, where the text gives one, an outcome. It carries a result direction and points at the passage that states the finding. A statement counts as a claim only when the work reports it as its own finding. A sentence that restates prior work, a hypothesis, a plan, or a goal is not a claim.

A claim needs an evidence span in the text of the source document. A finding that the annotator infers from a figure without a sentence in the text gets no label.

## One claim per result

Each measured result is one claim. A sentence that reports two measurements gives two claims, each with its own span. A sentence that reports the same measurement on two systems gives two claims, one per study. A claim never bundles two directions.

The dev fixture shows the rule: the sentence about zebrafish larvae in `work_bio_0001` gives one claim for survival and one claim for motor activity.

## Absent values

A field is absent when the passage and its section do not state the value. The annotator leaves the field null and does not guess from domain knowledge.

- A comparator is absent when the finding has no baseline in the text.
- A measurement is absent when the text names no measured quantity, which is common for EXISTENCE and MECHANISM claims.
- The result direction is never absent. UNKNOWN is the direction when the text states a result without a direction.
- A value is absent when the text gives a direction and no number.

Scoring treats null as a value of its own. A predicted value where the gold is null counts as a false positive. A predicted null where the gold has a value counts as a false negative.

## Ambiguous cases

- When two readings of a passage are both defensible, the annotator picks the more literal one and records the reason in the claim text.
- When the direction of a result is unclear, the direction is UNKNOWN, never a guess.
- When a passage can belong to two studies, the study is the one the surrounding paragraph describes.
- When the annotator cannot decide whether a statement is a finding, the statement gets no claim.
- When a sentence reports a result and its statistical test, the span covers both, and the claim records the p value as text.

## Normalization equivalence

Names carry the original text and a canonical form. Two values are equal for scoring when their canonical forms are equal after case folding and removal of surrounding whitespace.

- When a value has no canonical form, its original text takes its place under the same comparison.
- The rule applies to the subject, the method name, the comparator name and the measurement name.
- Predicates and outcomes compare as plain text under the same case folding.
- Claim types and result directions compare as enum values.
- Units are not scored in this increment.

Normalization rules are fixed before scoring (plan section 50). The annotator writes the canonical form that the normalization rules of the extraction branch produce for the same original text. Where no rule exists yet, the canonical form is the most common name in the field, in lower case, singular. The gold canonical form does not add information that the text lacks.

## Multiple studies per paper

A study is one coherent evaluation or analysis inside a work. A work with a cell culture experiment and an animal experiment has two studies, and each claim names its study through a study key. Study keys are unique across the dataset, so an evaluation maps them to predicted study IDs without a work lookup. A method, comparator or measurement that is correct but attached to the wrong study earns no relationship credit.

## Abstract-only limits

When the source level is ABSTRACT_ONLY, the annotator labels only what the abstract states. Values that the full text would give stay absent, and the gold document records the source level so a report can separate abstract-only scores from full-text scores. An abstract that reports a direction without a value gives a claim with a null value. METADATA_ONLY documents get no claims.

## Evidence spans and the overlap rule

The span is the shortest run of text that states the finding, and it stays inside one section. The span holds the direction and, when present, the value. It leaves out the sentence subject when the subject sits in another clause, so two claims from one sentence get two spans that do not cover each other.

A predicted claim matches a gold claim under the overlap rule:

- Both spans name the same section.
- The Jaccard index of their character ranges is at least 0.5. The index is the length of the intersection divided by the length of the union.
- Matching is one to one and greedy on the highest index.

An exact match has the same start and end offsets. A report gives the exact rate and the overlap rate separately, with the offsets of every overlap that is not exact. Two spans that cover different halves of one sentence do not match each other, because their index is 0.

## Query labels

A retrieval label lists every gold claim that answers the query, by claim key. A stance label assigns one of the six stance values and one comparability level to a query and claim pair (plan sections 37 and 39). An INCOMPATIBLE pair carries the stance INSUFFICIENTLY_COMPARABLE. A pair the annotator did not label has no stance, and a predicted stance for such a pair does not count.
