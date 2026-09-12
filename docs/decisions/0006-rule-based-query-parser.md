# ADR 0006: A rule based query parser instead of a model call

## Status
Accepted, 2026-09-12

## Context
Plan section 34 turns user text into a typed QueryProposition with a subject, a relationship, a measurement, a comparator and an expected direction. Plan section 47 names a QueryParser but does not say how it parses. A model call would read a proposition well, but it adds a provider dependency, a prompt version to record, network fixtures for the tests, and output that changes between runs. Plan section 36 starts retrieval simple and adds machinery only when a benchmark shows a failure.

## Decision
parse_query in `src/evidence_dossier/query/parser.py` is a fixed set of rules. It lowercases the text, drops a leading question word, and finds the first relationship verb from a table that maps each verb to a relationship label and an expected ResultDirection. The subject is the text before the verb. A comparator marker ("compared with", "versus", "than", "relative to") splits the rest into the measurement and the comparator. When no verb matches, the whole text becomes the subject and the relationship is "unknown".

Every rule that fires lands in parse_notes on the proposition. The API returns the notes, so a reader sees how the fields came about. The proposition keeps plain strings, not Term records: canonical names belong to normalize (ADR 0005), and query never imports it.

The query records QueryProposition, StanceAssessment and Dossier live in model, not in query. The store adds and gets them, and store imports nothing from query.

## Consequences
Easier: the parser is deterministic, needs no fixture and no key, and the parse tests state the exact fields. The rule table is short enough to read in one screen. A failed parse is visible in parse_notes rather than hidden in a model response.

Harder: the verb table covers a handful of relationships. A proposition phrased another way ("is associated with", "outperforms") parses with the relationship "unknown", and the stance classifier then answers INDIRECT because it has no expected direction. A model backed parser can replace this one behind the same function once the query benchmark shows the rules fail on real propositions.

## Alternatives considered
- **A model call behind the extraction provider adapter.** Rejected for now: it adds a prompt version, network fixtures and nondeterministic parses before the benchmark shows a need.
- **A dependency parser such as spaCy.** Rejected: a new heavy dependency for a parse that a verb table handles on the demo propositions.
- **Term records on the proposition.** Rejected: canonical names come from normalize, which query does not import, so the canonical side would stay empty.
