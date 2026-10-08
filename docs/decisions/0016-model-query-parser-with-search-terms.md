# ADR 0016: A model query parser that errors on failure and proposes search terms

## Status
Accepted, 2026-10-08. Replaces the fallback behavior of ADR 0012 for the model path. The parser is off by default.

## Context
The rule parser reads the words a researcher types into a search box only when a relationship verb from its table appears. The benchmark of ADR 0012 leaves 10 of 30 propositions unresolved. A natural sentence such as "endometriosis has less invasive ways to come up with a largely accurate diagnosis than laparoscopic surgery" parses as one subject with the relationship "unknown", no measurement and no comparator. The comparability step then has nothing to compare.

Retrieval has a second gap. It searches for the query words and nothing else, so a claim that says "Abeta" does not surface for a query that says "amyloid". The judge of ADR 0015 can only decide on claims that retrieval returns.

`ModelQueryParser` already existed and fell back to the rules when the model failed. It was never wired to the command line or the API, and the README says no real model has run it.

## Decision
`ModelQueryParser` asks a model for the proposition fields and for `search_terms`: at most 10 short words or phrases that a paper might use for the subject, the measurement or the comparator. Prompt `query-parse-v3` asks for the terms to leave out words the question already uses.

The parser no longer falls back. A call is retried once. A failure after that, a reply that is not one JSON object that fits the fields, or an unknown direction raises `QueryParseError` and logs the cause. The message names the cause and not the query text. A fallback would run the query on a parser the user did not ask for and hide the difference, which ADR 0013 and ADR 0015 also refuse.

Validated parses are cached in a folder, one file per query, keyed by sha256 of the model ID and the prompt. With no model callable the parser replays the folder, so a recorded query needs no network and no key.

`QueryProposition` gets `search_terms`, stored as a JSON column added by migration `0004_search_terms.sql`. Propositions stored earlier read as an empty list. `query_terms` in the retriever adds the tokens of the search terms to the FTS expression. Nothing else reads them: the judge and the annotator see the subject, the comparator and the measurement, so an alias the model invented cannot make a claim look comparable.

`search_evidence` takes an optional parser, and `evidence-dossier search --parse-model MODEL --parses DIR` selects the model path. The rules stay the default.

## Consequences
Easier: a sentence outside the verb table can still reach a typed proposition. Recall improves for synonyms, acronyms and long forms. A recorded query replays offline.

Harder: a parse costs a model call and can differ between runs, since the command line tool has no temperature setting. The first validated reply is cached. A wrong expected direction still decides the stance, so a parse error reaches the verdict. The stance rules model direction only, so "less invasive and as accurate" parses into one relationship and loses the second claim. Splitting a proposition into several is not part of this change.

The benchmark is the 30 labeled propositions of ADR 0012, which one author wrote, plus the queries of the judge benchmark. It reports agreement per field for the rules and for each model. It does not measure search terms, which have no gold labels: their effect shows in the retrieval counts only.

## Alternatives considered
- **Keep the fallback.** Rejected: the rules would answer in place of the model without a visible difference in the output.
- **Search terms from a fixed alias table.** Rejected: a table written for the demo corpus would overfit it and fail elsewhere.
- **Let the judge read the search terms.** Rejected: the terms come from a model that has not seen the claims, and a verdict built on them would be hard to audit.
- **Decompose a proposition into sub-propositions.** Deferred: it changes the model records and the dossier counts.
