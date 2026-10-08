# Judge labeling guidelines

Version 1. These rules precede the labels. An annotator applies them to every query and claim pair, and the judge benchmark scores against them. A rule change is a new guideline version, and labels made under an older version do not mix with newer ones in one split. The rules are written before any pair is labeled and before any model sees a pair.

## What the annotator sees

The pair sheet shows the same inputs the judge receives and nothing else:

- The query text and its parsed fields: subject, measurement, comparator.
- The claim fields: subject, method, comparator, measurement, outcome, claim type and research context.
- The evidence passage, and the title of the work.

The sheet shows no rule result, no model verdict and no stance. The key that links a sheet row to its source claim is a separate file and stays closed until all labels are written.

## What is labeled

Each pair gets one verdict for each of three dimensions. A dimension is skipped (left empty) when either side names nothing for it, because the engine already decides that case without a model.

| Dimension | Question |
| --- | --- |
| subject | Does the claim subject name the entity the query subject names? |
| comparator | Does the claim baseline name the baseline the query names? |
| measurement | Does the claim measure the quantity the query names? |

## Verdicts

- **match**: the passage or the fields establish that the two sides name the same thing, or the claim side is a named instance of the query side.
- **mismatch**: the two sides name different things, or the same thing in an opposite role or condition.
- **unknown**: the shown inputs do not settle it. Missing context is unknown, never a guess.

Measurement has three more verdicts, and each counts as not matched:

- **inverse**: the same quantity read the other way ("recovery rate" against "infection rate" is mismatch, but "survival" against "mortality" is inverse).
- **broader**: the claim measures something wider than the query names.
- **narrower**: the claim measures one part of what the query names.

## Directness

Evidence directness is not labeled. The engine derives it: a claim is direct when its measurement verdict is match and its claim type is not theoretical.

## Decision rules

1. Use only the shown inputs. World knowledge settles identity and synonymy only ("Abeta1-42" names the amyloid beta peptide). It never settles scope, so a peptide level does not establish "amyloid pathology".
2. A word that reverses the meaning decides the pair: with and without, early and late, increase and decrease, a drug and its control.
3. A claim whose subject and comparator are the reverse of the query's has the subject verdict mismatch. The stance rules never read roles.
4. A reference such as "the models" is match only when the passage or the work title names the entity. Otherwise it is unknown.
5. An acronym is match when the fields or the passage spell it out as the query term, and unknown when they do not.
6. When two readings stay defensible, the annotator picks unknown.

## Worked cases

| Query side | Claim side | Dimension | Verdict | Reason |
| --- | --- | --- | --- | --- |
| the same model without retrieval | same model with retrieval | comparator | mismatch | the condition is reversed |
| infection rate | recovery rate | measurement | mismatch | a different quantity that shares a word |
| retrieval augmentation | RAG models, with the passage spelling out retrieval-augmented generation | subject | match | the acronym is spelled out |
| retrieval augmentation | the models, passage names no method | subject | unknown | the reference is not resolved |
| amyloid pathology | intracellular Abeta1-42 level | measurement | narrower | one part of the pathology |
| factual hallucination | factual error rate | measurement | match | same quantity under the field's usual name |

## Pair sheet and splits

- A sheet row holds a pair ID, the shown inputs and an empty verdict column per dimension.
- Pairs split 24 to 16 by claim work and query, with the hash split of ADR 0004 and a new salt. The 16 test pairs are hashed before any model runs. Guidelines, prompts and thresholds change on the 24 development pairs only.
- Origin tags: `retrieved` for a pair drawn from the retrieval output, `reverse` for a query written from a claim. Both appear in the report apart from each other.
- The annotator relabels 15 pairs after 7 days without looking at earlier labels. Agreement between the two passes is self-consistency, not inter-annotator agreement.
- One annotator labeled the pairs, and the report says so.
