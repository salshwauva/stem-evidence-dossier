# ADR 0014: Comparator markers, a comparator gate on firm stances, and no rate suffix in the polarity table

## Status
Accepted, 2026-10-07. Amends ADR 0007: the suffix rule it describes is removed.

## Context
Four cases gave a firm stance on evidence that does not bear on the proposition. Each was reproduced on the claim `claim-supports` of the test corpus with one field changed.

1. A claim comparator "same model with retrieval" matched the proposition comparator "the same model without retrieval" as EXACT, and the stance was SUPPORTS. "with" and "without" are both stopwords in `query/text.py`, so token overlap sees the same words in both phrases.
2. A claim comparator "human experts" gave the level MODERATE, because the comparator dimension failed, and the stance was still SUPPORTS. The classifier only read the level to reject LOW and INCOMPATIBLE, so a result measured against another baseline counted as a result against the requested one.
3. Measurement matching (a claim measurement "recovery rate" against a proposition measurement "infection rate" overlaps on one of two words and passes the 0.5 threshold). ADR 0015 covers this case.
4. The suffix rule of ADR 0007 read every name that ends in "rate" or "error" as lower is better. "success rate", "pass rate", "survival rate", "recovery rate" and "hit rate" all came back LOWER_IS_BETTER, so an improved success rate contradicted "increases success rate".

## Decision
`query/text.py` gets `has_without`. It returns True when a phrase holds "without", "no", "not" or "non", False when it holds "with", and None otherwise. `_comparator` in `query/comparability.py` fails the dimension when both the proposition comparator and the claim comparator carry a marker and the markers differ. A phrase with no marker, such as "vanilla model", is not read as a mismatch. The word overlap rule is unchanged for every other case.

`_decide` in `query/stance.py` returns INDIRECT when the proposition names a comparator and the comparator dimension did not match. The check runs after the directness check and before the direction comparison, so it covers SUPPORTS, CONTRADICTS, MIXED and NULL alike. The reason names the requested comparator. A claim with no comparator against a proposition with one fails the dimension, so it also gives INDIRECT. A proposition with no comparator is not gated.

`query/polarity.py` drops the suffix rule. `polarity_of` looks up the exact folded key and returns None for any other name, so a comparison that needs a polarity gives INDIRECT with the existing reason. `POLARITY_VERSION` moves to `polarity-v3`. No entry was added. The seed table is the same.

## Consequences
Easier: a result against a different baseline or against the opposite condition no longer counts as support or contradiction. A rate with no entry is reported as missing a polarity instead of getting a guessed one.

Harder: fewer decided stances. A claim that reports against an unnamed baseline, or one phrased with a synonym for the requested baseline ("no augmentation" against "without retrieval"), now gives INDIRECT. The marker check only reads the six words above, so a baseline that expresses absence in other words is not caught. Rate measurements that were decided by the suffix rule now need an explicit table entry and a new version.

## Alternatives considered
- **Keep "with" and "without" as tokens in the overlap score.** Rejected: "same model with retrieval" still holds two of three words of "same model without retrieval", so it passes the 0.5 threshold.
- **Read every negation word as a mismatch against every phrase without one.** Rejected: "vanilla model" is a common way to name a baseline without retrieval, and the rule would reject it.
- **A new stance for a failed comparator.** Rejected: INDIRECT already means the claim bears on the proposition without answering it, and a new stance changes the model, the store and the API.
- **Keep the suffix rule and list exceptions.** Rejected: the rule answers the wrong question for every rate that counts good outcomes, and an exception list grows with each new measurement.
