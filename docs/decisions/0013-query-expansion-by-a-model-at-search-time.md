# ADR 0013: A model expands the query at search time, and retrieval is the only step that reads it

## Status
Accepted, 2026-10-02

## Context
Search parsed a proposition with rules and retrieved claims with SQLite FTS5 over its subject, measurement and comparator tokens. A paper that supports or contradicts a proposition often words it another way: another name for the method, an abbreviation, a related measurement, the opposite finding in other words. Keyword search over the proposition tokens misses those papers, and the rules cannot list the other wordings in advance.

## Decision
`query/expansion.py` adds `ModelQueryExpander`. It takes a callable that maps a prompt to text, so `query` imports no provider and holds no key, the same boundary as ADR 0012. It asks the model for up to 20 search terms and returns their tokens, minus the tokens the proposition already searches.

`Retriever.retrieve` takes `extra_terms` and searches the proposition tokens and the extra tokens together with one FTS5 OR expression. `search_evidence` takes an optional `expander`, and the expansion note joins `parse_notes`, so a stored proposition names the terms that widened its search.

The expansion changes which claims reach the candidate list and nothing else. The comparability engine and the stance classifier read the proposition and the claim, never the expansion.

The query text is untrusted, so the prompt wraps it between delimiters. The reply is untrusted too: it must validate into one object with a `terms` list, an extra field fails, and every term reaches FTS5 as lowercase letters and digits only. A provider error or a bad reply gives an empty expansion and a note that names the exception class and not its message.

The expander is off by default. `evidence-dossier search --expand-model MODEL` turns it on through the claude command line tool.

## Consequences
Easier: a claim whose wording differs from the proposition can reach the candidate list, and a failed model call leaves search exactly as it was.

Harder: a search with expansion makes a model call, takes seconds, and varies between runs. The evaluation record under `docs/evaluation/real-abstracts/` keeps the replies in `expansions.json`, so a score can be reproduced without a model. More terms widen the match, so the candidate list holds more claims that the gold labels do not mention.

Not done: the API routes do not take an expander yet, and stance still comes from rules.

## Alternatives considered
- **Embedding search.** Rejected for now: it adds an index, a model and a store column, and the expansion step needs none of them.
- **A model that reranks the candidates.** Left for the stance step, where a model reads each candidate passage anyway.
- **Let the model write the FTS5 expression.** Rejected: the reply is untrusted, and tokens are the narrowest thing the search needs from it.
