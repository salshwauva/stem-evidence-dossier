# Evaluation on 8 real abstracts

One run of the evaluate package on real text. Run date: 2026-10-02.

## Inputs

- 3 arXiv papers (1706.03762, 1412.6980, 1512.03385) and 5 PubMed papers (35124915, 35063214, 36613936, 37693076, 36855610).
- Every document is ABSTRACT_ONLY. PMC full text was not reachable from the run environment.
- Extraction ran through `evidence-dossier extract` with the `claude-sonnet-5-5` model.
- A Claude model wrote the gold labels from the stored abstract text, before it read the extractor output. No human labeled them.

## Results

Two runs on the same 8 abstracts and the same gold. The first run hit a span validation defect that stored no claims for one paper. The fix lets a plain space in a model quote match a no-break space in the stored text (`src/evidence_dossier/extract/validation.py`). The second run re-extracted that one paper. The other 7 papers kept their claims from the first run.

| measure | before the fix | after the fix |
| --- | --- | --- |
| gold claims | 30 | 30 |
| predicted claims | 34 | 38 |
| claim match, span overlap rule of the guidelines (Jaccard 0.5) | precision 47.1%, recall 53.3% | precision 50.0%, recall 63.3% |
| claim match, any span overlap | precision 64.7%, recall 73.3% | precision 65.8%, recall 83.3% |
| field micro precision and recall, matched and unmatched claims | 26.4% and 27.9% | 27.4% and 33.2% |
| stance accuracy over all 21 labeled pairs | 14.3% (3 of 21) | 33.3% (7 of 21) |
| stance accuracy over the pairs that got a prediction | 42.9% (3 of 7) | 53.8% (7 of 13) |
| stance macro F1 | 0.115 | 0.258 |
| retrieval Recall@5 | 0.306 | 0.639 |

`report.before-fix.md` and `report.md` hold the two full reports.

## With AI query expansion

Search ran again over the same store and gold, with `ModelQueryExpander` and the `claude-sonnet-5-5` model (ADR 0013). The extraction claims did not change. `expansions.json` holds the model replies, so `score_expanded.py` replays them without a model call.

| measure | rules and keywords | with expansion |
| --- | --- | --- |
| retrieval Recall@5 | 0.639 | 0.722 |
| retrieval Recall@10 | 0.722 | 0.722 |
| retrieval Precision@10 | 0.117 | 0.117 |
| stance accuracy over all 21 labeled pairs | 33.3% (7 of 21) | 33.3% (7 of 21) |
| stance macro F1 | 0.258 | 0.258 |
| predictions without a gold label | 29 | 52 |

Expansion widened retrieval a little and left stance alone, which is expected, because stance still comes from rules and reads the claim, not the expansion. Eight labeled pairs still get no prediction. Six of them belong to gold claims whose predicted span did not overlap the gold span enough to match, so the evaluation could not link a retrieved claim to its gold key. The other two are unrelated controls that search rightly did not return. The extraction prompt says "choose a passage" and gives no length, while the annotation guidelines ask for the shortest run of text that states the finding. That mismatch lowers every score that depends on a claim match, and it is the first thing to settle before the next run.

## Read these before you quote a number

- N is 30 claims. One claim moves a rate by about 3 points.
- The gold spans are clause sized and the extractor spans are sentence sized. The strict match rule drops some correct claims for that reason alone, so the strict figures read low.
- The field scores compare predicate and outcome as exact text after case folding. The gold phrasing is one choice among several, so those fields score low even when the extraction is right.
- The second run re-extracted one paper, and a model reply varies between calls. The jump from the fix mixes the fix with that variation.
- 8 of 21 stance pairs still got no prediction because retrieval did not return the claim. The stance score mostly reflects retrieval misses and the rule based classifier.
- The gold labeler and the extractor are the same model family, which usually inflates agreement.

## Files

- `gold/`: documents, retrievals and stances, in the layout of `tests/fixtures/evaluate/`.
- `make_gold.py`: the label specs. It finds each span by its text and writes the offsets. It reads `dossier.db`.
- `score.py`: runs `evaluate_store` over the gold and the store.
- The SQLite store is not committed. Re-ingesting the 8 identifiers rebuilds it.
