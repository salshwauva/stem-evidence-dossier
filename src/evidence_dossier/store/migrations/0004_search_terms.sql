-- Words a model proposed for the retrieval step of a query (ADR 0016). They widen the
-- search and nothing else. Propositions stored before this file keep an empty list.
ALTER TABLE query_propositions ADD COLUMN search_terms TEXT NOT NULL DEFAULT '[]';
