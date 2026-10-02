# Evaluation report

- Model: claude-sonnet-5-5
- Prompt version: v1
- Schema version: v1
- Split: dev
- Created at: 2026-10-02T22:45:34.058495+00:00
- Note: The papers are 8 real abstracts: 3 from arXiv and 5 from PubMed. Every document is ABSTRACT_ONLY.
- Note: The gold labels were written by Claude, not by a human annotator, from the stored abstract text and before the extractor output was read.
- Note: The extractor also ran on a Claude model, so a score here is a same-family comparison and probably reads high.

## Extraction

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.382 | 0.433 | 0.406 | 30 |
| subject | 0.265 | 0.300 | 0.281 | 30 |
| predicate | 0.088 | 0.100 | 0.094 | 30 |
| outcome | 0.147 | 0.167 | 0.156 | 30 |
| method | 0.308 | 0.276 | 0.291 | 29 |
| comparator | 0.500 | 0.444 | 0.471 | 9 |
| measurement | 0.312 | 0.250 | 0.278 | 20 |
| result_direction | 0.324 | 0.367 | 0.344 | 30 |
| micro | 0.264 | 0.279 | 0.271 | 208 |
| macro | 0.291 | 0.292 | 0.290 | 208 |

### By domain: BIOLOGY

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.333 | 0.312 | 0.323 | 16 |
| subject | 0.067 | 0.062 | 0.065 | 16 |
| predicate | 0.000 | 0.000 | 0.000 | 16 |
| outcome | 0.133 | 0.125 | 0.129 | 16 |
| method | 0.286 | 0.133 | 0.182 | 15 |
| comparator | 0.500 | 0.250 | 0.333 | 4 |
| measurement | 0.125 | 0.083 | 0.100 | 12 |
| result_direction | 0.200 | 0.188 | 0.194 | 16 |
| micro | 0.163 | 0.135 | 0.148 | 111 |
| macro | 0.206 | 0.144 | 0.166 | 111 |

### By domain: COMPUTER_SCIENCE

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.421 | 0.571 | 0.485 | 14 |
| subject | 0.421 | 0.571 | 0.485 | 14 |
| predicate | 0.158 | 0.214 | 0.182 | 14 |
| outcome | 0.158 | 0.214 | 0.182 | 14 |
| method | 0.316 | 0.429 | 0.364 | 14 |
| comparator | 0.500 | 0.600 | 0.545 | 5 |
| measurement | 0.500 | 0.500 | 0.500 | 8 |
| result_direction | 0.421 | 0.571 | 0.485 | 14 |
| micro | 0.336 | 0.443 | 0.382 | 97 |
| macro | 0.362 | 0.459 | 0.403 | 97 |

### By source level: ABSTRACT_ONLY

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.382 | 0.433 | 0.406 | 30 |
| subject | 0.265 | 0.300 | 0.281 | 30 |
| predicate | 0.088 | 0.100 | 0.094 | 30 |
| outcome | 0.147 | 0.167 | 0.156 | 30 |
| method | 0.308 | 0.276 | 0.291 | 29 |
| comparator | 0.500 | 0.444 | 0.471 | 9 |
| measurement | 0.312 | 0.250 | 0.278 | 20 |
| result_direction | 0.324 | 0.367 | 0.344 | 30 |
| micro | 0.264 | 0.279 | 0.271 | 208 |
| macro | 0.291 | 0.292 | 0.290 | 208 |

### Claim matching

- Unmatched gold claims: work_5c58342a230665a3:c1, work_5c58342a230665a3:c2, work_5c58342a230665a3:c3, work_5c58342a230665a3:c4, work_5c58342a230665a3:c5, work_5c58342a230665a3:c6, work_5c58342a230665a3:c10, work_4627097f8362928c:c3, work_4627097f8362928c:c4, work_a1a0262a54cd0bbc:c3, work_a1a0262a54cd0bbc:c4, work_f911b46a09ec5d13:c1, work_f911b46a09ec5d13:c2, work_f911b46a09ec5d13:c3
- Unmatched predicted claims: work_6d41d2f09c026403_v1_c1, work_6d41d2f09c026403_v1_c2, work_6d41d2f09c026403_v1_c3, work_6d41d2f09c026403_v1_c4, work_6d41d2f09c026403_v1_c5, work_ecdc742ad2d21fbc_v1_c1, work_ecdc742ad2d21fbc_v1_c3, work_551d55b26e0cb4a5_v1_c1, work_551d55b26e0cb4a5_v1_c2, work_5c58342a230665a3_v1_c1, work_5c58342a230665a3_v1_c2, work_5c58342a230665a3_v1_c3, work_5c58342a230665a3_v1_c4, work_4627097f8362928c_v1_c6, work_a1a0262a54cd0bbc_v1_c2, work_a1a0262a54cd0bbc_v1_c4, work_a1a0262a54cd0bbc_v1_c5, work_8c83c39cd1afa399_v1_c2

### Field errors

| gold | predicted | field | gold value | predicted value |
| --- | --- | --- | --- | --- |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c6 | claim_type | PERFORMANCE | THEORETICAL |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | claim_type | EFFECT | NON_EXISTENCE |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | claim_type | PERFORMANCE | ROBUSTNESS |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | subject | ipconazole | gabaergic inhibitory neurons |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | subject | gln768 and arg976 | gln768 and arg976 of cas9 |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | subject | ipconazole | glutamatergic excitatory and dopaminergic neurons |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | subject | ipconazole | ipconazole-treated (2 μg/ml) embryos |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | subject | 152-layer residual nets | residual nets with 152 layers |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | subject | plantar warts | planter warts |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c4 | subject | deep residual representations | extremely deep representations |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | predicate | dysregulated | were dysregulated by ipconazole, as shown by interrupted gad1b expression |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | predicate | establishes | establishes new single-model state-of-the-art |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | predicate | achieves | achieves error on |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | predicate | won | won 1st place on |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | predicate | act synergistically in | act synergistically, according to a proposed model |
| work_4627097f8362928c:c7 | work_4627097f8362928c_v1_c5 | predicate | won | won 1st places on |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | predicate | did not affect | remained unaffected by ipconazole |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | predicate | caused | exhibited caspase-independent cell death |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | predicate | have lower complexity than | are deeper than yet lower in complexity than |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | predicate | were the commonest type | were the commonest type by site among patients with cutaneous warts |
| work_8c83c39cd1afa399:c1 | work_8c83c39cd1afa399_v1_c1 | predicate | was related to more | was more effective than cryotherapy for complete resolution of |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | predicate | applies successfully to | generalizes to |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c4 | predicate | improves | yield relative improvement on |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | outcome | gabaergic inhibitory neurons | dysregulated gabaergic inhibitory neurons |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | outcome | bleu | bleu score on wmt 2014 english-to-french translation |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | outcome | error | error on the imagenet test set |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | outcome | ilsvrc 2015 classification | ilsvrc 2015 classification ranking |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | outcome | cas9 configurational space | synergy between the two residues |
| work_4627097f8362928c:c7 | work_4627097f8362928c_v1_c5 | outcome | ilsvrc and coco 2015 competition tasks | competition ranking |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | outcome | glutamatergic excitatory and dopaminergic neurons | no effect on glutamatergic excitatory and dopaminergic neurons |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | outcome | complexity | depth and complexity relative to vgg nets |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | outcome | wart type | distribution of wart sites |
| work_6d41d2f09c026403:c1 | work_6d41d2f09c026403_v1_c7 | outcome | optimization performance | other stochastic optimization methods |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | outcome | bleu | bleu score on wmt 2014 english-to-german translation |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | method | ipconazole treatment | (absent) |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | method | residual nets | ensemble of residual nets |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | method | residual nets | ensemble of residual nets |
| work_4627097f8362928c:c7 | work_4627097f8362928c_v1_c5 | method | residual nets | deep residual nets |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | method | ipconazole treatment | (absent) |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | method | ipconazole treatment | (absent) |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c4 | method | residual nets | extremely deep representations (deep residual nets) |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | comparator | previous single-model results | (absent) |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | comparator | existing best results, including ensembles | (absent) |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | measurement | cell death | (absent) |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | measurement | complexity | depth |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | measurement | (absent) | proportion of warts by site |
| work_8c83c39cd1afa399:c1 | work_8c83c39cd1afa399_v1_c1 | measurement | complete resolution of warts | response as complete or partial or no resolution of the wart |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c4 | measurement | object detection performance | relative improvement |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | result_direction | UNKNOWN | MIXED |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | result_direction | UNKNOWN | OBSERVED |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | result_direction | INCREASED | OBSERVED |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | result_direction | DECREASED | MIXED |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | result_direction | IMPROVED | OBSERVED |

### Relationships

- Matched claims: 16
- Correct relationships: 4
- Rate: 0.250

| gold | predicted | reason |
| --- | --- | --- |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | method differs |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | comparator differs |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | method differs |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | method differs |
| work_4627097f8362928c:c7 | work_4627097f8362928c_v1_c5 | method differs |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | method differs |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | method differs; measurement differs |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | measurement differs |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | measurement differs |
| work_8c83c39cd1afa399:c1 | work_8c83c39cd1afa399_v1_c1 | measurement differs |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c4 | method differs; measurement differs |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | comparator differs |

### Evidence spans

- Gold claims: 30
- Exact matches: 2 (rate 0.067)
- Overlap matches: 16 (rate 0.533)

| gold | predicted | gold offsets | predicted offsets |
| --- | --- | --- | --- |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | 638 to 718 | 638 to 719 |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | 720 to 788 | 720 to 789 |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | 986 to 1048 | 986 to 1049 |
| work_4627097f8362928c:c7 | work_4627097f8362928c_v1_c5 | 1163 to 1286 | 1157 to 1287 |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c6 | 776 to 906 | 768 to 906 |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | 1343 to 1412 | 1335 to 1412 |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | 1474 to 1551 | 1460 to 1552 |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c3 | 530 to 636 | 494 to 637 |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | 933 to 1010 | 933 to 1038 |
| work_8c83c39cd1afa399:c1 | work_8c83c39cd1afa399_v1_c1 | 1084 to 1208 | 1039 to 1209 |
| work_6d41d2f09c026403:c1 | work_6d41d2f09c026403_v1_c7 | 943 to 1034 | 908 to 1035 |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | 1037 to 1135 | 973 to 1136 |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c4 | 992 to 1065 | 942 to 1066 |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | 563 to 720 | 563 to 642 |

## Retrieval

- Recall@5: 0.306
- Recall@10: 0.389
- Precision@10: 0.067

| query | relevant | returned | recall@5 | recall@10 | precision@10 |
| --- | --- | --- | --- | --- | --- |
| q1 | 2 | 2 | 0.000 | 0.000 | 0.000 |
| q2 | 3 | 7 | 0.333 | 0.333 | 0.100 |
| q3 | 2 | 7 | 0.500 | 1.000 | 0.200 |
| q4 | 1 | 7 | 0.000 | 0.000 | 0.000 |
| q5 | 1 | 5 | 1.000 | 1.000 | 0.100 |
| q6 | 1 | 2 | 0.000 | 0.000 | 0.000 |

## Stance

- Labeled pairs: 21
- Pairs without a prediction: 14
- Predictions without a label: 23
- Macro F1: 0.115

| class | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| SUPPORTS | not assessable | 0.000 | 0.000 | 7 |
| CONTRADICTS | not assessable | not assessable | not assessable | 0 |
| NULL | not assessable | 0.000 | 0.000 | 1 |
| MIXED | not assessable | not assessable | not assessable | 0 |
| INDIRECT | 0.000 | 0.000 | 0.000 | 5 |
| INSUFFICIENTLY_COMPARABLE | 0.600 | 0.375 | 0.462 | 8 |

### Confusion matrix (rows gold, columns predicted)

| gold | SUPPORTS | CONTRADICTS | NULL | MIXED | INDIRECT | INSUFFICIENTLY_COMPARABLE |
| --- | --- | --- | --- | --- | --- | --- |
| SUPPORTS | 0 | 0 | 0 | 0 | 2 | 1 |
| CONTRADICTS | 0 | 0 | 0 | 0 | 0 | 0 |
| NULL | 0 | 0 | 0 | 0 | 0 | 0 |
| MIXED | 0 | 0 | 0 | 0 | 0 | 0 |
| INDIRECT | 0 | 0 | 0 | 0 | 0 | 1 |
| INSUFFICIENTLY_COMPARABLE | 0 | 0 | 0 | 0 | 0 | 3 |

## Comparability

- Accuracy: 0.571

| query | claim | predicted | reason |
| --- | --- | --- | --- |
