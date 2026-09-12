# ADR 0007: A null stance of its own and a versioned measurement polarity table

## Status
Accepted, 2026-09-12

## Context
The stance classifier in `src/evidence_dossier/query/stance.py` turned a comparable claim into one of the six stances of plan section 39. Two of its rules did not follow the plan.

The first rule read the statistical significance flag. A claim with the direction UNCHANGED or NOT_OBSERVED became CONTRADICTS when the flag was true, and NULL when it was false. Plan section 39 lists NULL next to CONTRADICTS as a separate stance, and plan section 21 keeps UNCHANGED and NOT_OBSERVED apart from the directions that oppose each other. A significant null result is still a null result. The significance flag says how well the study measured the absence of an effect, not that the study found the opposite effect.

The second rule read an expected DECREASED against a reported IMPROVED as SUPPORTS, with no other test. The comment said the rule holds when the proposition reduces an unwanted outcome. That is an assumption about the measurement, and the classifier had no way to check it. It is right for "reduces the factual error rate" and wrong for "reduces accuracy". Plan section 21 gives INCREASED and DECREASED for magnitude and IMPROVED and WORSENED for quality, and the two families only line up once the reader knows which way the measurement points.

Plan section 7 works one query through the six stances, and its Contradicts entry reads "Result: no improvement". That wording sends a null result to CONTRADICTS.

## Decision
UNCHANGED and NOT_OBSERVED map to NULL, whatever the significance flag says. The flag goes into the reason sentence as "reported as significant" or "no significance reported", so a reader sees the strength of the null result without the stance changing.

A new module `src/evidence_dossier/query/polarity.py` holds the measurement polarity. `POLARITY_VERSION` names the table version, `Polarity` gives the two values LOWER_IS_BETTER and HIGHER_IS_BETTER, and `TABLE` maps a folded measurement name to one of them. `fold` reuses the token rules of `query/text.py`, so a key matches a claim measurement whatever its case, its spacing or its hyphens. The seed entries come from the measurements that the plan examples and the test corpus name. The lookup tries the exact key first. It then applies one suffix rule: a name whose last token is "rate" or "error" counts as lower is better.

The classifier calls the table only when it needs to cross the two direction families, that is when the expected direction is IMPROVED or WORSENED and the reported direction is not, or the other way round. It restates the quality direction as the magnitude direction that the polarity gives it, and then compares. An expected DECREASED against a reported IMPROVED is SUPPORTS on a lower is better measurement and CONTRADICTS on a higher is better one. A same family pair such as DECREASED against DECREASED, or an opposite pair such as INCREASED against DECREASED, needs no table. When the crossing is needed and the table does not hold the measurement, the stance is INDIRECT and the reason names the measurement and the table version.

`StanceAssessment` in `src/evidence_dossier/model/query.py` gets no new field. The table `stance_assessments` in `store/migrations/0002_query.sql` names its columns, so a field would need a new migration and a wider change than this fix. Every reason string therefore ends with the sentence that names the table version, and a stored assessment still says which table decided its stance.

The decision overrides the plan section 7 wording "Result: no improvement" under Contradicts. Plan sections 21 and 39 are the normative lists, and section 7 is one worked example. An example that folds NULL into CONTRADICTS hides the difference between a study that found the opposite effect and a study that found nothing, which is the difference a dossier reader most needs.

## Consequences
Easier: a null result reads as a null result, and the dossier no longer counts it as evidence against the proposition. The polarity assumption is a table a reader can check and extend, not a comment in a branch. The version in the reason says which table produced a stored stance, so an old assessment stays readable after the table changes.

Harder: the table is small, and a measurement outside it sends a cross family comparison to INDIRECT rather than to a stance. That is the intended failure, but it lowers the count of decided stances until the table grows. Every new or changed entry needs a new POLARITY_VERSION, because stored assessments name the version that decided them. The suffix rule covers names such as "refusal rate" and "annotation error" and nothing else, so most additions are new keys.

## Alternatives considered
- **Keep the significance flag in the stance and split NULL from CONTRADICTS by the flag.** Rejected: plan section 39 gives NULL its own value, and the flag describes the measurement, not the direction of the finding.
- **Read the polarity from the claim text or the predicate.** Rejected: the text says the study improved something, which is the question, not the answer. A table states the assumption once and keeps it out of the classifier.
- **Add a polarity field to Measurement and fill it during extraction.** Rejected for now: it needs a model change, a migration and an extraction rule, and the table answers the stance question today. The field stays open for a later change.
- **Add a `polarity_version` field to StanceAssessment.** Rejected: the stance assessment table names its columns, so the field needs a migration that this fix does not carry. The reason sentence records the version instead.
