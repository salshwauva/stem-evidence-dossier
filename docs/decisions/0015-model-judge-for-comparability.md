# ADR 0015: A model judge for the meaning based comparability dimensions

## Status
Accepted, 2026-10-07. Reverses the line in ADR 0012 that keeps a model call out of the evidence verdicts. The judge is off by default and stays off until the benchmark gate passes.

## Context
On the real demo corpus both demo queries returned 20 claims, and every one was INSUFFICIENTLY_COMPARABLE. The comparability engine matches by word overlap, and the claims name things differently from the queries:

- The extractor copied "the models" from an abstract, and the query says "retrieval augmentation".
- The query says "amyloid pathology" and the claim measures "intracellular Abeta1-42".
- The query says "infection rate" and the claim measures "recovery rate". They share one of two words, so the 0.5 overlap threshold passed them (ADR 0014 lists this case).

A prompt change that asks the extractor for full noun phrases (`claims-v2`) removes the anaphora. It cannot bridge a synonym or a difference in scope.

ADR 0006 and ADR 0012 kept a model out of the ask path until a benchmark showed the rules failing. The demo run is that evidence. ADR 0012 also states that a model call under the parse must not become a model call under the evidence verdicts. This ADR reverses that sentence for three dimensions and keeps it for the rest.

## Decision
`ModelComparator` in `src/evidence_dossier/query/model_comparator.py` judges three dimensions for each retrieved claim: subject, comparator and measurement. A dimension is asked only when both sides name something. Otherwise the rules decide it as before.

Each judged dimension gets one verdict: match, mismatch or unknown. Measurement can also get inverse, broader or narrower. Only match counts as matched. Every verdict carries a quote and a one sentence reason. A verdict other than unknown needs a quote that appears in the inputs shown to the model, and a verdict without one is set to unknown. The reason shows in the comparability reasons and in the output.

The rest of the pipeline stays deterministic:

- The method dimension follows the subject verdict. It affected only the EXACT level.
- Evidence directness is derived: the measurement verdict is match and the claim type is not theoretical.
- The with and without comparator marker of ADR 0014 still vetoes a judged comparator match.
- The comparator gate, the polarity table and the direction comparison are unchanged, and the model never sees the result direction.

A failed call is retried once. A reply that is not one JSON object that fits the schema, that omits or adds a claim, or that judges a dimension that was not asked counts as a failed call. After the retry the judge raises `ComparatorError`, logs the claim IDs and the cause, and `search_evidence` stores nothing. There is no fallback to word overlap, because a silent fallback would return the original false matches without saying so.

Validated judgments are cached in a folder, one file per batch, keyed by sha256 of the model ID and the prompt. The prompt holds the prompt version, the schema version, the question, every claim field the model sees and the passage setting, so the key cannot drift from the inputs. With no model callable the judge replays the folder, so tests and the demo need no network and no key. The key includes the model ID because the extraction replay key does not, and a benchmark compares several models on one prompt.

The `claude` command line tool offers no temperature setting, so a repeated run can differ. The cache stores the first validated reply, and the benchmark reports how often a repeat changes a verdict.

The judge reaches users through `evidence-dossier search --judge MODEL --judgments DIR`. Batch size and the passage setting are benchmark variables and not flags.

The benchmark decides which model and which batch size ship (`docs/judge-labeling-guidelines.md`, `scripts/judge_benchmark.py`). A judge arm passes the gate when it makes no more false matches than the rules arm, finds at least half of the labeled matches, and agrees with the labels on matched or not at least as often as the rules arm. The recall floor blocks an arm that answers unknown everywhere. The gate is fixed on the development pairs and run once on the test pairs.

## Consequences
Easier: a claim that says "the models" or names a synonym can reach a firm stance, and the reason says what the judge decided and why. The stance rules still decide the direction, so the model cannot flip a result.

Harder: search with the judge costs one or more model calls per query and takes seconds per call. A wrong match verdict can still produce a wrong firm stance, and the reason does not name the judge, so the comparability reasons are the audit trail. The README line that stance is a rule result stays true only for the direction step. Labels come from one annotator, so the benchmark supports agreement with that reader on this corpus and nothing wider.

Open: the closest demo claim has the comparator "state-of-the-art chatbots" against "the same model without retrieval". A strict judge may call that a mismatch, and the comparator gate then gives INDIRECT. The demo may show few firm stances, and the README states what it shows.

## Alternatives considered
- **Query side alias expansion, one model call per query.** Not chosen first: it adds no per-claim reasoning. It stays a candidate arm if the judge fails the gate.
- **Fix only the extraction prompt.** Done as `claims-v2`, and kept. It cannot bridge a synonym or a scope difference.
- **A model that assigns the stance.** Rejected: it would put the direction and the polarity under the model, which is where a false SUPPORTS costs most.
- **Fall back to the rules on a failed call.** Rejected: ADR 0013 refuses to discard data silently, and the fallback returns the false matches that motivated this change.
- **Embeddings or a cross encoder.** Rejected for now: a new dependency that still cannot separate a reversed condition or a scope difference.
