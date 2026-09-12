# ADR 0008: The evaluation route passes the search to evaluate as a callable

## Status
Accepted, 2026-09-12

## Context
Plan section 48 lists GET /evaluation, and plan section 50 asks one report to cover extraction, retrieval, stance and comparability. The extraction scores read the stored claims, which `evaluate` can load from the store. The retrieval and the stance scores need search results, which only `query` produces.

The import rule in the architecture document says that a subpackage never imports a sibling. A direct import of `query` from `evaluate` would break that rule and would tie the scorers to one retrieval implementation. The extraction package already met this problem and solved it by taking the normalizer as an argument (ADR 0005).

## Decision
`evaluate_store` in `src/evidence_dossier/evaluate/run.py` takes a `search` argument. The callable takes the store and one query text and returns the results in rank order, each one a `SearchHit` with a claim ID, a stance, a comparability level and a reason. `evaluate` therefore imports `model` and `store` only, and it scores whatever search the caller hands it.

The adapter that turns `search_evidence` into that callable lives in `src/evidence_dossier/api/app.py`, because `api` is the layer that may import both packages. The architecture document names this second exception next to the existing one for `query`.

A stored claim reaches its gold key through the evidence span match of `matching.py`, never through an ID convention. The same match gives the gold study key to stored study ID map that the relationship score needs. The extractor is free to name its claims and its studies as it likes.

## Consequences
Easier: a test passes a fixed ranking and scores a whole run without the query package, a store or a network call. A second retrieval implementation scores against the same gold labels with no change to `evaluate`. The scorers stay a leaf of the import graph.

Harder: the caller writes the adapter, so two callers can pass rankings that differ. The report names the search only through the notes that the caller passes, so a reader of a report alone does not see which search produced the retrieval numbers.

## Alternatives considered
- **A direct import of `query` from `evaluate`.** Rejected: it breaks the import rule, and it makes every evaluation test build a real store and run the parser.
- **The whole run inside `api`.** Rejected: the route would hold the mapping from stored claims to gold keys, which belongs next to the span matching rule in `evaluate`.
- **A protocol class for a retriever instead of a callable.** Rejected for now: one function with two arguments needs no class, and a protocol invites the retrieval interface to grow before a second implementation asks for it.
