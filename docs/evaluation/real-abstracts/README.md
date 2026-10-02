# Evaluation on 8 real abstracts

One run of the evaluate package on real text. Run date: 2026-10-02.

## Inputs

- 3 arXiv papers (1706.03762, 1412.6980, 1512.03385) and 5 PubMed papers (35124915, 35063214, 36613936, 37693076, 36855610).
- Every document is ABSTRACT_ONLY. PMC full text was not reachable from the run environment.
- Extraction ran through `evidence-dossier extract` with the `claude-sonnet-5-5` model.
- A Claude model wrote the gold labels from the stored abstract text, before it read the extractor output. No human labeled them.

## Results

| measure | value |
| --- | --- |
| gold claims | 30 |
| predicted claims | 34 |
| claim match, span overlap rule of the guidelines (Jaccard 0.5) | precision 47.1%, recall 53.3% |
| claim match, any span overlap | precision 64.7%, recall 73.3% |
| field micro precision and recall, matched and unmatched claims | 26.4% and 27.9% |
| stance accuracy over all 21 labeled pairs | 14.3% (3 of 21) |
| stance accuracy over the 7 pairs that got a prediction | 42.9% (3 of 7) |
| stance macro F1 | 0.115 |

`report.md` holds the full report.

## Read these before you quote a number

- N is 30 claims. One claim moves a rate by about 3 points.
- The gold spans are clause sized and the extractor spans are sentence sized. The strict match rule drops some correct claims for that reason alone, so the strict figures read low.
- The field scores compare predicate and outcome as exact text after case folding. The gold phrasing is one choice among several, so those fields score low even when the extraction is right.
- `work_f911b46a09ec5d13_v1` failed validation and stored no claims. The stored text holds non-breaking spaces and the model reply holds plain spaces, so no span matched. That is a pipeline defect, and it costs 3 gold claims of recall.
- 14 of 21 stance pairs got no prediction because retrieval did not return the claim. The stance score mostly reflects retrieval misses.
- The gold labeler and the extractor are the same model family, which usually inflates agreement.

## Files

- `gold/`: documents, retrievals and stances, in the layout of `tests/fixtures/evaluate/`.
- `make_gold.py`: the label specs. It finds each span by its text and writes the offsets. It reads `dossier.db`.
- `score.py`: runs `evaluate_store` over the gold and the store.
- The SQLite store is not committed. Re-ingesting the 8 identifiers rebuilds it.
