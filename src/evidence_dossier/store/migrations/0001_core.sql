-- Core records: research works, work links, source documents, sections,
-- studies, extraction runs and evidence claims (plan section 46).
-- Nested claim parts are JSON that Pydantic validates on the way in and out.
-- ADR 0002 explains the layout.

CREATE TABLE works (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    doi TEXT,
    abstract TEXT,
    publication_date TEXT,
    venue TEXT,
    authors TEXT NOT NULL,              -- JSON list of authors with affiliations
    external_identifiers TEXT NOT NULL  -- JSON object from scheme to value
);

CREATE TABLE work_links (
    source_work_id TEXT NOT NULL REFERENCES works (id),
    relation TEXT NOT NULL,
    target_work_id TEXT NOT NULL REFERENCES works (id),
    PRIMARY KEY (source_work_id, relation, target_work_id)
);

CREATE TABLE source_documents (
    id TEXT PRIMARY KEY,
    research_work_id TEXT NOT NULL REFERENCES works (id),
    version INTEGER NOT NULL,
    source_level TEXT NOT NULL,
    source_format TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE sections (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents (id),
    ordinal INTEGER NOT NULL,
    section_type TEXT NOT NULL,
    heading TEXT,
    text TEXT NOT NULL
);

CREATE TABLE studies (
    id TEXT PRIMARY KEY,
    research_work_id TEXT NOT NULL REFERENCES works (id),
    description TEXT NOT NULL
);

CREATE TABLE extraction_runs (
    id TEXT PRIMARY KEY,
    source_document_id TEXT NOT NULL REFERENCES source_documents (id),
    model_identifier TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    raw_response TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    errors TEXT NOT NULL                -- JSON list of error messages
);

CREATE TABLE claims (
    id TEXT PRIMARY KEY,
    research_work_id TEXT NOT NULL REFERENCES works (id),
    study_id TEXT NOT NULL REFERENCES studies (id),
    extraction_run_id TEXT REFERENCES extraction_runs (id),
    claim_type TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    normalized_claim TEXT,
    subject_original TEXT NOT NULL,
    subject_canonical TEXT,
    predicate TEXT NOT NULL,
    outcome TEXT,
    research_context TEXT NOT NULL,     -- JSON
    method TEXT,                        -- JSON
    comparator TEXT,                    -- JSON
    measurement TEXT,                   -- JSON
    result TEXT NOT NULL,               -- JSON
    -- The evidence span. Its research work is the research work of the claim.
    section_id TEXT NOT NULL REFERENCES sections (id),
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    source_text TEXT NOT NULL,
    -- Copies of values from the JSON columns and from the source document,
    -- so retrieval can filter on real columns.
    domain TEXT NOT NULL,
    method_canonical TEXT,
    comparator_canonical TEXT,
    measurement_canonical TEXT,
    result_direction TEXT NOT NULL,
    source_level TEXT NOT NULL
);

CREATE INDEX claims_research_work_id_idx ON claims (research_work_id);
CREATE INDEX claims_study_id_idx ON claims (study_id);
CREATE INDEX claims_domain_idx ON claims (domain);
CREATE INDEX claims_claim_type_idx ON claims (claim_type);
