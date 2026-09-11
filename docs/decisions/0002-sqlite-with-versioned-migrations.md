# ADR 0002: stdlib sqlite3 with versioned SQL migrations and no ORM

## Status
Accepted, 2026-09-11

## Context
Plan section 46 picks SQLite for the first implementation. Four branches start from this one and run in parallel: ingestion, extraction, evaluation and query. The query branch adds SQLite FTS5 full-text search, which needs virtual tables and triggers in plain SQL. Each branch must extend the schema without a code change to the migration runner.

## Decision
The store uses stdlib sqlite3 with no ORM. The schema lives in numbered SQL files under `src/evidence_dossier/store/migrations/`. The runner applies each file once, in filename order, and records its name in a schema_version table. Each file runs in one transaction together with its schema_version row, so a failed file leaves no partial schema. This branch writes 0001_core.sql, and the query branch adds 0002_query.sql.

The tables follow the records. A flat record maps each field to a column. Nested claim parts are JSON text that Pydantic validates on the way in and out: the research context, method, comparator, measurement and result, with their domain attributes. Works keep authors and external identifiers as JSON, and extraction runs keep their errors as JSON.

The claims table copies the fields that retrieval filters on into real columns: domain, claim_type, subject_canonical, method_canonical, comparator_canonical, measurement_canonical, result_direction and source_level. add_claim writes these copies from the JSON parts and from the source document. No method updates a claim after insert, so the copies cannot drift.

Evidence spans are columns on claims: section_id, start_offset, end_offset and source_text. Each claim has exactly one span. section_id is a foreign key to sections, and Store turns foreign keys on for every connection. The research work of a stored span is the research work of its claim, because add_claim refuses a span that names another work.

## Consequences
Easier: the Pydantic models stay the only schema for nested parts. FTS5 tables and triggers are plain SQL in a migration file. A schema change is one new file.

Harder: store.py holds hand-written mapping code for each record. A filter on a value inside a JSON column needs json_extract, so a common filter gets a real column in a new migration. The filter columns repeat data from the JSON columns.

## Alternatives considered
- **SQLAlchemy or another ORM.** Rejected: it adds a second schema next to the Pydantic models, and FTS5 virtual tables fall outside it.
- **Alembic for migrations.** Rejected: it expects SQLAlchemy models.
- **Evidence spans in their own table.** Considered. Plan section 44 later links methodological reporting flags to spans, and those flags could share span rows. Today one claim has one span, so columns avoid a join and a synthetic span ID. A later migration can move spans to their own table.
- **One JSON column for each whole record.** Rejected: foreign keys and FTS5 need real columns.
