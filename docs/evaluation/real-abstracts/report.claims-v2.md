# Evaluation report

- Model: claude-cli/claude-sonnet-5-5
- Prompt version: claims-v2
- Schema version: core-1
- Split: dev
- Created at: 2026-10-02T23:23:05.012037+00:00
- Note: The papers are 8 real abstracts: 3 from arXiv and 5 from PubMed. Every document is ABSTRACT_ONLY.
- Note: The gold labels were written by Claude, not by a human annotator, from the stored abstract text and before the extractor output was read.
- Note: The extractor also ran on a Claude model, so a score here is a same-family comparison and probably reads high.

## Extraction

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.586 | 0.567 | 0.576 | 30 |
| subject | 0.276 | 0.267 | 0.271 | 30 |
| predicate | 0.103 | 0.100 | 0.102 | 30 |
| outcome | 0.250 | 0.233 | 0.241 | 30 |
| method | 0.381 | 0.276 | 0.320 | 29 |
| comparator | 0.455 | 0.556 | 0.500 | 9 |
| measurement | 0.500 | 0.550 | 0.524 | 20 |
| result_direction | 0.552 | 0.533 | 0.542 | 30 |
| micro | 0.379 | 0.361 | 0.369 | 208 |
| macro | 0.388 | 0.385 | 0.385 | 208 |

### By domain: BIOLOGY

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.588 | 0.625 | 0.606 | 16 |
| subject | 0.059 | 0.062 | 0.061 | 16 |
| predicate | 0.000 | 0.000 | 0.000 | 16 |
| outcome | 0.412 | 0.438 | 0.424 | 16 |
| method | 0.222 | 0.133 | 0.167 | 15 |
| comparator | 0.600 | 0.750 | 0.667 | 4 |
| measurement | 0.500 | 0.583 | 0.538 | 12 |
| result_direction | 0.588 | 0.625 | 0.606 | 16 |
| micro | 0.354 | 0.360 | 0.357 | 111 |
| macro | 0.371 | 0.402 | 0.384 | 111 |

### By domain: COMPUTER_SCIENCE

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.583 | 0.500 | 0.538 | 14 |
| subject | 0.583 | 0.500 | 0.538 | 14 |
| predicate | 0.250 | 0.214 | 0.231 | 14 |
| outcome | 0.000 | 0.000 | 0.000 | 14 |
| method | 0.500 | 0.429 | 0.462 | 14 |
| comparator | 0.333 | 0.400 | 0.364 | 5 |
| measurement | 0.500 | 0.500 | 0.500 | 8 |
| result_direction | 0.500 | 0.429 | 0.462 | 14 |
| micro | 0.412 | 0.361 | 0.385 | 97 |
| macro | 0.406 | 0.371 | 0.387 | 97 |

### By source level: ABSTRACT_ONLY

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.586 | 0.567 | 0.576 | 30 |
| subject | 0.276 | 0.267 | 0.271 | 30 |
| predicate | 0.103 | 0.100 | 0.102 | 30 |
| outcome | 0.250 | 0.233 | 0.241 | 30 |
| method | 0.381 | 0.276 | 0.320 | 29 |
| comparator | 0.455 | 0.556 | 0.500 | 9 |
| measurement | 0.500 | 0.550 | 0.524 | 20 |
| result_direction | 0.552 | 0.533 | 0.542 | 30 |
| micro | 0.379 | 0.361 | 0.369 | 208 |
| macro | 0.388 | 0.385 | 0.385 | 208 |

### Claim matching

- Unmatched gold claims: work_5c58342a230665a3:c2, work_5c58342a230665a3:c3, work_5c58342a230665a3:c10, work_4627097f8362928c:c3, work_4627097f8362928c:c4, work_4627097f8362928c:c7, work_a1a0262a54cd0bbc:c3, work_a1a0262a54cd0bbc:c4
- Unmatched predicted claims: work_ecdc742ad2d21fbc_v1_c1, work_551d55b26e0cb4a5_v1_c1, work_a1a0262a54cd0bbc_v1_c2, work_a1a0262a54cd0bbc_v1_c4, work_a1a0262a54cd0bbc_v1_c5, work_f911b46a09ec5d13_v1_c2, work_8c83c39cd1afa399_v1_c2

### Field errors

| gold | predicted | field | gold value | predicted value |
| --- | --- | --- | --- | --- |
| work_f911b46a09ec5d13:c1 | work_f911b46a09ec5d13_v1_c1 | claim_type | EFFECT | COMPARISON |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | claim_type | EFFECT | COMPARISON |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | claim_type | PERFORMANCE | THEORETICAL |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | claim_type | PERFORMANCE | ROBUSTNESS |
| work_f911b46a09ec5d13:c2 | work_f911b46a09ec5d13_v1_c3 | claim_type | EFFECT | COMPARISON |
| work_5c58342a230665a3:c6 | work_5c58342a230665a3_v1_c4 | subject | ipconazole | ipconazole treatment |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | subject | ipconazole | gabaergic inhibitory neurons |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | subject | ipconazole | glutamatergic excitatory and dopaminergic neurons |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | subject | ipconazole | ipconazole-treated embryos |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | subject | plantar warts | planter warts |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | subject | gln768 and arg976 | gln768 and arg976 of cas9 |
| work_f911b46a09ec5d13:c1 | work_f911b46a09ec5d13_v1_c1 | subject | vitamin d supplement | vitamin d supplement group |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | subject | vitamin d supplement and fortified oil | study groups |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | subject | ipconazole | ipconazole-treated embryos |
| work_5c58342a230665a3:c5 | work_5c58342a230665a3_v1_c3 | subject | ipconazole | ipconazole treatment |
| work_5c58342a230665a3:c1 | work_5c58342a230665a3_v1_c1 | subject | ipconazole | ipconazole-exposed zebrafish larvae |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | subject | deep residual representations | extremely deep representations |
| work_f911b46a09ec5d13:c2 | work_f911b46a09ec5d13_v1_c3 | subject | vitamin d supplement and fortified oil | vitamin d fortified oil group (vitamin d sufficient subgroup) |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c4 | subject | 152-layer residual nets | residual nets with 152 layers |
| work_5c58342a230665a3:c6 | work_5c58342a230665a3_v1_c4 | predicate | increased | increased erk1/2 phosphorylation |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | predicate | dysregulated | were dysregulated by ipconazole |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | predicate | did not affect | remained unaffected by ipconazole |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | predicate | caused | exhibited caspase-independent cell death |
| work_8c83c39cd1afa399:c1 | work_8c83c39cd1afa399_v1_c1 | predicate | was related to more | was more strongly related to complete resolution of warts than |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | predicate | were the commonest type | were the commonest type according to site of warts |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | predicate | act synergistically in | act synergistically, as described by a proposed model |
| work_f911b46a09ec5d13:c1 | work_f911b46a09ec5d13_v1_c1 | predicate | increased | increased serum 25(oh)d more than |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | predicate | did not change | did not differ in mean differences of |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | predicate | won | won 1st place on |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | predicate | has a regret bound comparable to | has a regret bound comparable to best known results |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | predicate | applies successfully to | generalizes to |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | predicate | reduced | showed reduced expression of mitochondrial antioxidants and mitochondrial genome maintenance and function genes |
| work_5c58342a230665a3:c5 | work_5c58342a230665a3_v1_c3 | predicate | reduced | reduced hsp70 expression |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | predicate | establishes | establishes new single-model state-of-the-art |
| work_5c58342a230665a3:c1 | work_5c58342a230665a3_v1_c1 | predicate | reduced | showed reduced locomotive activity |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | predicate | improves | improve |
| work_f911b46a09ec5d13:c2 | work_f911b46a09ec5d13_v1_c3 | predicate | increased | increased serum 25(oh)d more than |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c4 | predicate | have lower complexity than | are deeper than but have lower complexity than |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | outcome | gabaergic inhibitory neurons | gad1b expression |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | outcome | caspase-independent cell death | cell death |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | outcome | wart type | proportion of patients with planter warts |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | outcome | cas9 configurational space | synergy between the two residues |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | outcome | pth, bap and ctx | bone turnover markers pth, bap, ctx |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | outcome | error | 3.57% error on the imagenet test set |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | outcome | ilsvrc 2015 classification | 1st place on the ilsvrc 2015 classification task |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | outcome | convergence rate | convergence rate regret bound |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | outcome | english constituency parsing | application to english constituency parsing |
| work_6d41d2f09c026403:c1 | work_6d41d2f09c026403_v1_c2 | outcome | optimization performance | (absent) |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | outcome | mitochondrial genome maintenance and function genes | superoxide dismutases 1 and 2 and mitochondrial genome maintenance and function genes |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | outcome | bleu | bleu score on wmt 2014 english-to-french translation |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | outcome | object detection performance | 28% relative improvement on coco object detection |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c4 | outcome | complexity | lower complexity despite 8x greater depth |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | outcome | bleu | bleu score on wmt 2014 english-to-german translation |
| work_5c58342a230665a3:c6 | work_5c58342a230665a3_v1_c4 | method | ipconazole treatment | (absent) |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | method | ipconazole treatment | (absent) |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | method | ipconazole treatment | (absent) |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | method | ipconazole treatment | (absent) |
| work_f911b46a09ec5d13:c1 | work_f911b46a09ec5d13_v1_c1 | method | 1000 iu vitamin d supplement | vitamin d supplement |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | method | vitamin d supplement and fortified oil | (absent) |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | method | residual nets | ensemble of residual nets |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | method | residual nets | ensemble of residual nets |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | method | ipconazole treatment | molecular profiling |
| work_5c58342a230665a3:c5 | work_5c58342a230665a3_v1_c3 | method | ipconazole treatment | (absent) |
| work_5c58342a230665a3:c1 | work_5c58342a230665a3_v1_c1 | method | ipconazole exposure | behavioral monitoring |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | method | residual nets | extremely deep residual representations |
| work_f911b46a09ec5d13:c2 | work_f911b46a09ec5d13_v1_c3 | method | vitamin d supplement and fortified oil | vitamin d fortified oil |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | comparator | control | (absent) |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | comparator | best known results | best known results under the online convex optimization framework |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | comparator | previous single-model results | (absent) |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | comparator | existing best results, including ensembles | (absent) |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | measurement | cell death | caspase-independent cell death |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | measurement | (absent) | proportion of patients with planter warts |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | measurement | bone turnover markers | mean differences of pth, bap, and ctx |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | measurement | regret bound | regret bound on the convergence rate |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | measurement | gene expression | expression of superoxide dismutases 1 and 2 and mitochondrial genome maintenance and function genes |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | measurement | object detection performance | relative improvement |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | result_direction | UNKNOWN | MIXED |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | result_direction | INCREASED | OBSERVED |
| work_ecdc742ad2d21fbc:c1 | work_ecdc742ad2d21fbc_v1_c2 | result_direction | UNKNOWN | OBSERVED |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | result_direction | UNCHANGED | OBSERVED |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | result_direction | IMPROVED | OBSERVED |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | result_direction | IMPROVED | OBSERVED |

### Relationships

- Matched claims: 22
- Correct relationships: 5
- Rate: 0.227

| gold | predicted | reason |
| --- | --- | --- |
| work_5c58342a230665a3:c6 | work_5c58342a230665a3_v1_c4 | method differs |
| work_5c58342a230665a3:c7 | work_5c58342a230665a3_v1_c5 | method differs |
| work_5c58342a230665a3:c8 | work_5c58342a230665a3_v1_c6 | method differs |
| work_5c58342a230665a3:c9 | work_5c58342a230665a3_v1_c7 | method differs; measurement differs |
| work_8c83c39cd1afa399:c2 | work_8c83c39cd1afa399_v1_c3 | measurement differs |
| work_f911b46a09ec5d13:c1 | work_f911b46a09ec5d13_v1_c1 | method differs |
| work_f911b46a09ec5d13:c3 | work_f911b46a09ec5d13_v1_c4 | method differs; comparator differs; measurement differs |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | method differs |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | method differs |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | comparator differs; measurement differs |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | method differs; measurement differs |
| work_5c58342a230665a3:c5 | work_5c58342a230665a3_v1_c3 | method differs |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | comparator differs |
| work_5c58342a230665a3:c1 | work_5c58342a230665a3_v1_c1 | method differs |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | method differs; measurement differs |
| work_f911b46a09ec5d13:c2 | work_f911b46a09ec5d13_v1_c3 | method differs |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | comparator differs |

### Evidence spans

- Gold claims: 30
- Exact matches: 9 (rate 0.300)
- Overlap matches: 22 (rate 0.733)

| gold | predicted | gold offsets | predicted offsets |
| --- | --- | --- | --- |
| work_4627097f8362928c:c1 | work_4627097f8362928c_v1_c1 | 638 to 718 | 638 to 719 |
| work_4627097f8362928c:c6 | work_4627097f8362928c_v1_c2 | 720 to 788 | 720 to 789 |
| work_6d41d2f09c026403:c2 | work_6d41d2f09c026403_v1_c1 | 776 to 906 | 768 to 906 |
| work_a1a0262a54cd0bbc:c5 | work_a1a0262a54cd0bbc_v1_c6 | 1037 to 1135 | 986 to 1135 |
| work_6d41d2f09c026403:c1 | work_6d41d2f09c026403_v1_c2 | 943 to 1034 | 975 to 1034 |
| work_5c58342a230665a3:c4 | work_5c58342a230665a3_v1_c2 | 880 to 1019 | 804 to 1019 |
| work_5c58342a230665a3:c5 | work_5c58342a230665a3_v1_c3 | 1114 to 1152 | 1093 to 1152 |
| work_a1a0262a54cd0bbc:c2 | work_a1a0262a54cd0bbc_v1_c3 | 774 to 892 | 774 to 850 |
| work_5c58342a230665a3:c1 | work_5c58342a230665a3_v1_c1 | 614 to 709 | 610 to 764 |
| work_4627097f8362928c:c2 | work_4627097f8362928c_v1_c3 | 992 to 1065 | 942 to 1066 |
| work_f911b46a09ec5d13:c2 | work_f911b46a09ec5d13_v1_c3 | 1025 to 1169 | 1089 to 1169 |
| work_4627097f8362928c:c5 | work_4627097f8362928c_v1_c4 | 530 to 636 | 579 to 636 |
| work_a1a0262a54cd0bbc:c1 | work_a1a0262a54cd0bbc_v1_c1 | 563 to 720 | 563 to 642 |

## Retrieval

- Recall@5: 0.889
- Recall@10: 0.889
- Precision@10: 0.133

| query | relevant | returned | recall@5 | recall@10 | precision@10 |
| --- | --- | --- | --- | --- | --- |
| q1 | 2 | 5 | 1.000 | 1.000 | 0.200 |
| q2 | 3 | 4 | 0.333 | 0.333 | 0.100 |
| q3 | 2 | 6 | 1.000 | 1.000 | 0.200 |
| q4 | 1 | 7 | 1.000 | 1.000 | 0.100 |
| q5 | 1 | 7 | 1.000 | 1.000 | 0.100 |
| q6 | 1 | 6 | 1.000 | 1.000 | 0.100 |

## Stance

- Labeled pairs: 21
- Pairs without a prediction: 7
- Predictions without a label: 21
- Macro F1: 0.326

| class | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| SUPPORTS | 1.000 | 0.429 | 0.600 | 7 |
| CONTRADICTS | not assessable | not assessable | not assessable | 0 |
| NULL | not assessable | 0.000 | 0.000 | 1 |
| MIXED | not assessable | not assessable | not assessable | 0 |
| INDIRECT | 0.000 | 0.000 | 0.000 | 5 |
| INSUFFICIENTLY_COMPARABLE | 0.667 | 0.750 | 0.706 | 8 |

### Confusion matrix (rows gold, columns predicted)

| gold | SUPPORTS | CONTRADICTS | NULL | MIXED | INDIRECT | INSUFFICIENTLY_COMPARABLE |
| --- | --- | --- | --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 0 | 0 | 2 | 1 |
| CONTRADICTS | 0 | 0 | 0 | 0 | 0 | 0 |
| NULL | 0 | 0 | 0 | 0 | 0 | 1 |
| MIXED | 0 | 0 | 0 | 0 | 0 | 0 |
| INDIRECT | 0 | 0 | 0 | 0 | 0 | 1 |
| INSUFFICIENTLY_COMPARABLE | 0 | 0 | 0 | 0 | 0 | 6 |

## Comparability

- Accuracy: 0.357

| query | claim | predicted | reason |
| --- | --- | --- | --- |
| q4 | work_5c58342a230665a3:c6 | LOW | Comparability is LOW because the measurement dimension does not match. The stance rules use polarity table polarity-v2. |
