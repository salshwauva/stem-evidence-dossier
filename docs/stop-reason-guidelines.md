# Stop reason guidelines

Version 1, 2026-09-30. These rules precede the labels. An annotator applies them to every note on the gold sheet, and the classifier evaluation scores against them. A rule change is a new guideline version, and labels made under an older version do not mix with newer ones in one split.

## What is labeled

The Why Stopped field of a ClinicalTrials.gov record (`protocolSection.statusModule.whyStopped`). The registry asks for it when a record has the status TERMINATED, WITHDRAWN or SUSPENDED. Sponsors fill it in as free text, and the median note is under 40 characters.

One note gets one primary label. The annotator reads the note text only. The gold sheet shows no status, phase, sponsor or title, so a label cannot follow the pattern the dashboard is meant to test. No rule below depends on anything except the words of the note.

A record with an empty note is not labeled. It is counted as "no reason given" and left out of every class share.

## Classes

| Id | Name | Applies when the note gives as its reason |
| --- | --- | --- |
| `accrual` | Enrollment or accrual | A recruitment shortfall. The text uses a shortfall word: low, slow, poor, insufficient, inadequate, lack of, unable, difficulty, challenges, failure to, not enough eligible patients. |
| `funding_business` | Funding or business | Money that ended or was never obtained. A sponsor that changes its strategy or priorities, stops developing the drug or program, is acquired, closes or goes bankrupt. A company or funder that ends its support, whether money or drug. |
| `safety` | Safety | Adverse events, toxicity, tolerability, a safety recommendation, or a safety difference between arms or schedules. |
| `interim_efficacy` | Interim efficacy results | The trial's own data show no benefit, too little activity, futility, a drug exposure too low to work, or a benefit large enough to stop early. |
| `logistics_external` | Logistics or external | A cause outside the study design and the sponsor's strategy. COVID-19. A drug, device or piece of equipment that is unavailable or whose supply is disrupted. A regulatory or ethics refusal, hold or lapsed approval. Contract delays. Data system problems. An investigator who left, retired or moved. A closed site. The results of another trial, or a new standard of care, that made the question moot. |
| `protocol_change` | Protocol change or replaced | The study was amended, redesigned, split, merged into another study or replaced by another record. A hold that waits on a protocol amendment. |
| `other_unclear` | Other or unclear | Everything else. A note that names who decided and gives no reason. A note that states only a status. A stated reason that fits no class above. |

## Rules

1. **Text only.** The label follows the words of the note. Status, phase, sponsor and title play no part.
2. **Who decided is not why.** "Sponsor decision", "Promotor decision", "PI request", "PI choice" and "Sponsor and investigator's decision" are `other_unclear`. When a reason follows the decision maker, the reason decides: "Sponsor Decision related to study drug supply" is `logistics_external`, and "Investigator decided to halt study due to low accrual" is `accrual`.
3. **The first stated reason is primary.** When a note gives a second, different reason, the annotator records its class in `label2`. Scoring uses the primary label only. The share of notes with a `label2` is reported.
4. **A denied reason is not a reason.** "Not due to safety reasons", "no safety signals" and "not a consequence of any safety concern" remove safety from the note. The remaining reason decides.
5. **Zero enrolled is a status, not a cause.** "No participants enrolled", "no subjects enrolled", "No enrollment", "No patient accrual", "never opened", "not initiated" and "not activated" are `other_unclear`. A shortfall word makes the note `accrual`: "Lack of enrollment", "unable to recruit", "Recruitment challenges".
6. **Support ended is business, supply broken is logistics.** A company or funder that ends or withdraws its support, money or drug, is `funding_business`. A supply that is disrupted, or an item that is unavailable, is `logistics_external`.
7. **This trial or another trial.** `interim_efficacy` needs results from this trial. A result from another trial is `logistics_external`.
8. **An interim analysis without a direction is unclear.** "Decision made based on Interim Analysis Results" and "DSMB recommendation" are `other_unclear`. When the note gives the direction (no efficacy, toxicity, benefit), the direction decides.
9. **Investigator departure.** An investigator who left, retired, moved or died is `logistics_external`. An investigator who requested or chose to stop falls under rule 2.
10. **Holds.** A suspended study takes the class of what it waits on. Waiting for funding is `funding_business`. Waiting for an amendment is `protocol_change`. Waiting for a regulator is `logistics_external`. A pause with no stated cause is `other_unclear`.
11. **Goal reached.** "Accrual goal met" and "The number of inclusion was reached normally" state that the study reached its target. They are `other_unclear`.
12. **Spelling and menu text.** Misspellings and translated words ("Promotor" for sponsor) do not change the class. The prefix "Other - ", which the registry menu adds, is ignored.

## Recording labels

The gold sheet has three columns for the annotator.

- `label`: the primary class id. Required for every note with text.
- `label2`: the class id of a second, different reason the note states. Optional.
- `unsure`: set to 1 when two classes both fit and no rule decides between them. The two ids go in the notes column. Optional.

The report gives the share of notes with a `label2`, the share marked `unsure`, and the share of each class among notes with text.

## Worked examples

Every note is verbatim from the registry, with its spelling. The notes read while drafting these rules are excluded from the gold sheet.

| Note | Label | Reason |
| --- | --- | --- |
| Slow accrual | `accrual` | shortfall word |
| unable to rectuir | `accrual` | shortfall word, rule 12 |
| Lack of enrollment | `accrual` | shortfall word, rule 5 |
| Low accrual and Merck discontinuing funding and drug supply | `accrual` | first reason, `label2` is `funding_business` |
| Poor accrual and the field has moved on. | `accrual` | first reason, `label2` is `logistics_external` |
| Funding unavailable to perform study. | `funding_business` | money |
| company focus on other projects | `funding_business` | sponsor priorities |
| The Sponsor has discontinued the development of tesetaxel | `funding_business` | program stopped |
| Sorrento Therapeutics filed for chapter 11 bankruptcy. | `funding_business` | company closed |
| Seeking further funding before resuming the study. | `funding_business` | rule 10 |
| withdrawal of support for drug supply | `funding_business` | rule 6 |
| The early termination was based on a business decision that FAZ053 would no longer be formulated and was not a consequence of any safety concern. | `funding_business` | rule 4 |
| Terminated due to safety | `safety` | safety |
| Sorafenib administered in the combination with pemetrexed-carboplatin appears to enhance thrombocytopenia compared to historical data. | `safety` | toxicity |
| Lack of efficacy after interim analysis | `interim_efficacy` | no benefit |
| lack of activity and G3-4 toxicity at interim analysis | `interim_efficacy` | first reason, `label2` is `safety` |
| DSMB recommendation due to lack of efficacy. There were no safety signals. | `interim_efficacy` | rule 4 |
| Study was halted prematurely due to insufficient efficacy. Not due to safety reasons. | `interim_efficacy` | rule 4 |
| DSMB recommendation | `other_unclear` | rule 8 |
| Decision made based on Interim Analysis Results | `other_unclear` | rule 8 |
| because the sunitinib showed futility in anotehr trial | `logistics_external` | rule 7 |
| COVID-19 | `logistics_external` | external event |
| PI left Moffitt | `logistics_external` | rule 9 |
| Equipment unavailable | `logistics_external` | rule 6 |
| The supply of IP is disrupted | `logistics_external` | rule 6 |
| Sponsor Decision related to study drug supply | `logistics_external` | rule 2 |
| refusal of the ansm | `logistics_external` | regulatory refusal |
| FDA reviewing | `logistics_external` | rule 10 |
| Change in trial design | `protocol_change` | redesign |
| This study has been incorporated into the Relmada REL-NDV01-303 study. | `protocol_change` | merged |
| Pending amendment to open further Cohorts | `protocol_change` | rule 10 |
| Sponsor decision | `other_unclear` | rule 2 |
| PI Request | `other_unclear` | rule 2 |
| No participants enrolled | `other_unclear` | rule 5 |
| Study withdrawn before enrolling first patient | `other_unclear` | rule 5 |
| Accrual goal met | `other_unclear` | rule 11 |

## How these rules were made

A sample of 300 notes with text, 120 terminated, 120 withdrawn and 60 suspended, was read before the rules were written. The notes come from the trials that pass the dashboard's oncology cohort rule (definition 1) in the first page of registry results for each status, drawn with a fixed seed. The first page is not a random draw from the registry, so the sample supports the rules and supports no prevalence figure.

The sample showed three things that shaped the classes.

- About 1 note in 11 (27 of 300 by a keyword count) describes an amendment, redesign, merger or replacement. Without `protocol_change` these notes would fill `other_unclear` and hide the real reasons.
- About 1 note in 27 (11 of 300) names a decision maker and no reason. Rule 2 sends them to `other_unclear`.
- About 1 note in 15 (20 of 300) reports that nobody enrolled or that the study never opened. Rule 5 sends them to `other_unclear`, because for a withdrawn record that is the definition of the status.

## Known limits

- One annotator labels the sheet, so no agreement between annotators exists.
- Rule 5 is a judgment call. A reader who counts "No enrollment" as an accrual reason gets a higher `accrual` share among withdrawn records.
- Rule 3 makes the primary label depend on the order of the words, and the order is the sponsor's choice.
- Notes that say less than one sentence cannot carry a class, so a share of `other_unclear` is expected.
