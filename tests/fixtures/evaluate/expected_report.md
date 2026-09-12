# Evaluation report

- Model: extractor-model-a
- Prompt version: claims-v1
- Schema version: core-1
- Split: dev
- Created at: 2026-09-12T06:00:00+00:00
- Note: The papers, the gold labels and the predictions are invented test fixtures.
- Note: The predictions were written by hand from the gold labels with deliberate errors.

## Extraction

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.833 | 0.714 | 0.769 | 7 |
| subject | 0.667 | 0.571 | 0.615 | 7 |
| predicate | 0.833 | 0.714 | 0.769 | 7 |
| outcome | 0.833 | 0.714 | 0.769 | 7 |
| method | 0.833 | 0.714 | 0.769 | 7 |
| comparator | 0.833 | 0.833 | 0.833 | 6 |
| measurement | 0.667 | 0.571 | 0.615 | 7 |
| result_direction | 0.667 | 0.571 | 0.615 | 7 |
| micro | 0.771 | 0.673 | 0.718 | 55 |
| macro | 0.771 | 0.676 | 0.720 | 55 |

### By domain: BIOLOGY

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 1.000 | 0.750 | 0.857 | 4 |
| subject | 0.667 | 0.500 | 0.571 | 4 |
| predicate | 1.000 | 0.750 | 0.857 | 4 |
| outcome | 1.000 | 0.750 | 0.857 | 4 |
| method | 1.000 | 0.750 | 0.857 | 4 |
| comparator | 1.000 | 1.000 | 1.000 | 3 |
| measurement | 1.000 | 0.750 | 0.857 | 4 |
| result_direction | 0.667 | 0.500 | 0.571 | 4 |
| micro | 0.917 | 0.710 | 0.800 | 31 |
| macro | 0.917 | 0.719 | 0.804 | 31 |

### By domain: COMPUTER_SCIENCE

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.667 | 0.667 | 0.667 | 3 |
| subject | 0.667 | 0.667 | 0.667 | 3 |
| predicate | 0.667 | 0.667 | 0.667 | 3 |
| outcome | 0.667 | 0.667 | 0.667 | 3 |
| method | 0.667 | 0.667 | 0.667 | 3 |
| comparator | 0.667 | 0.667 | 0.667 | 3 |
| measurement | 0.333 | 0.333 | 0.333 | 3 |
| result_direction | 0.667 | 0.667 | 0.667 | 3 |
| micro | 0.625 | 0.625 | 0.625 | 24 |
| macro | 0.625 | 0.625 | 0.625 | 24 |

### By source level: ABSTRACT_ONLY

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 0.500 | 0.500 | 0.500 | 2 |
| subject | 0.000 | 0.000 | 0.000 | 2 |
| predicate | 0.500 | 0.500 | 0.500 | 2 |
| outcome | 0.500 | 0.500 | 0.500 | 2 |
| method | 0.500 | 0.500 | 0.500 | 2 |
| comparator | 0.500 | 0.500 | 0.500 | 2 |
| measurement | 0.500 | 0.500 | 0.500 | 2 |
| result_direction | 0.500 | 0.500 | 0.500 | 2 |
| micro | 0.438 | 0.438 | 0.438 | 16 |
| macro | 0.438 | 0.438 | 0.438 | 16 |

### By source level: FULL_TEXT

| field | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| claim_type | 1.000 | 0.800 | 0.889 | 5 |
| subject | 1.000 | 0.800 | 0.889 | 5 |
| predicate | 1.000 | 0.800 | 0.889 | 5 |
| outcome | 1.000 | 0.800 | 0.889 | 5 |
| method | 1.000 | 0.800 | 0.889 | 5 |
| comparator | 1.000 | 1.000 | 1.000 | 4 |
| measurement | 0.750 | 0.600 | 0.667 | 5 |
| result_direction | 0.750 | 0.600 | 0.667 | 5 |
| micro | 0.938 | 0.769 | 0.845 | 39 |
| macro | 0.938 | 0.775 | 0.847 | 39 |

### Claim matching

- Unmatched gold claims: work_bio_0001:c3, work_cs_0002:c1
- Unmatched predicted claims: p7

### Field errors

| gold | predicted | field | gold value | predicted value |
| --- | --- | --- | --- | --- |
| work_bio_0002:c1 | p4 | subject | trl9 knockout | knockout of the gene trl9 |
| work_cs_0001:c2 | p6 | measurement | latency | latency per query |
| work_bio_0001:c2 | p2 | result_direction | UNCHANGED | DECREASED |

### Relationships

- Matched claims: 5
- Correct relationships: 3
- Rate: 0.600

| gold | predicted | reason |
| --- | --- | --- |
| work_cs_0001:c2 | p6 | measurement differs |
| work_bio_0001:c2 | p2 | study s-bio1-cells is not the study of bio1-larvae |

### Evidence spans

- Gold claims: 7
- Exact matches: 4 (rate 0.571)
- Overlap matches: 5 (rate 0.714)

| gold | predicted | gold offsets | predicted offsets |
| --- | --- | --- | --- |
| work_bio_0001:c2 | p2 | 135 to 174 | 140 to 174 |

## Retrieval

- Recall@5: 0.444
- Recall@10: 0.667
- Precision@10: 0.133

| query | relevant | returned | recall@5 | recall@10 | precision@10 |
| --- | --- | --- | --- | --- | --- |
| q1 | 3 | 7 | 0.333 | 1.000 | 0.300 |
| q2 | 1 | 2 | 1.000 | 1.000 | 0.100 |
| q3 | 1 | 0 | 0.000 | 0.000 | 0.000 |

## Stance

- Labeled pairs: 9
- Pairs without a prediction: 1
- Predictions without a label: 1
- Macro F1: 0.522

| class | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| SUPPORTS | 0.667 | 1.000 | 0.800 | 2 |
| CONTRADICTS | not assessable | 0.000 | 0.000 | 1 |
| NULL | 1.000 | 1.000 | 1.000 | 2 |
| MIXED | not assessable | 0.000 | 0.000 | 1 |
| INDIRECT | 0.500 | 1.000 | 0.667 | 1 |
| INSUFFICIENTLY_COMPARABLE | 1.000 | 0.500 | 0.667 | 2 |

### Confusion matrix (rows gold, columns predicted)

| gold | SUPPORTS | CONTRADICTS | NULL | MIXED | INDIRECT | INSUFFICIENTLY_COMPARABLE |
| --- | --- | --- | --- | --- | --- | --- |
| SUPPORTS | 2 | 0 | 0 | 0 | 0 | 0 |
| CONTRADICTS | 1 | 0 | 0 | 0 | 0 | 0 |
| NULL | 0 | 0 | 2 | 0 | 0 | 0 |
| MIXED | 0 | 0 | 0 | 0 | 0 | 0 |
| INDIRECT | 0 | 0 | 0 | 0 | 1 | 0 |
| INSUFFICIENTLY_COMPARABLE | 0 | 0 | 0 | 0 | 1 | 1 |

## Comparability

- Accuracy: 0.625

| query | claim | predicted | reason |
| --- | --- | --- | --- |
| q1 | work_bio_0002:c1 | LOW | both works test a genetic or chemical change in a whole organism |
