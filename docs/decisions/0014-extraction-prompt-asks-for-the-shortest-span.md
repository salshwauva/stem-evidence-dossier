# ADR 0014: The extraction prompt asks for the shortest span (claims-v2)

## Status
Accepted, 2026-10-02

## Context
The annotation guidelines say an evidence span is the shortest run of text that states the finding, and that two claims from one sentence get two spans that do not cover each other. The span match of the evaluation is built on that rule: two spans match when their Jaccard index is at least 0.5.

The prompt claims-v1 said only "choose a passage that occurs once in its section". On 8 real abstracts the model returned whole sentences. A sentence span next to a clause span of the same finding has an index below 0.5, so the evaluation counted a correct claim as one missed gold claim and one false positive. Every score that depends on a claim match read low for that reason, and the retrieval and stance scores read low with it, because a retrieved claim reaches its gold label through the span match.

## Decision
The prompt is claims-v2. It adds one rule: the passage is the shortest run of text that states the finding, usually a clause and not the whole sentence. It holds the direction and the value when the text gives one, and it leaves out words that belong to another claim.

The rule restates the annotation guidelines in the prompt. It was written before the claims-v2 run and from the guidelines, not from the claims-v1 output.

## Consequences
Easier: the extractor and the labels now follow one definition of a span, so a match score measures extraction and not a disagreement about span length.

Harder: a claims-v1 run and a claims-v2 run are different prompts. Their scores sit side by side in `docs/evaluation/real-abstracts/` and are not one series. The 8 abstracts of that folder now count as dev data for this prompt, so a score on them says nothing about unseen papers.

## Alternatives considered
- **Loosen the span match.** Rejected: the 0.5 index is the rule of the guidelines, and a looser rule would hide a real mismatch instead of removing it.
- **Rewrite the gold spans to whole sentences.** Rejected: the guidelines ask for short spans because a sentence often holds two claims, and a sentence span cannot keep them apart.
