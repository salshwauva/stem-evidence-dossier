-- Query records: full-text search over claims, query propositions, stance
-- assessments and dossier snapshots (plan sections 36, 39, 45 and 46).
-- ADR 0002 explains the layout.

-- External content FTS5 index over the claim text columns. The claims table
-- keeps the text, and the three triggers keep the index in sync. A claim row
-- never changes after insert, so the update trigger only covers a manual fix.
CREATE VIRTUAL TABLE claims_fts USING fts5 (
    claim_text,
    normalized_claim,
    subject_original,
    subject_canonical,
    outcome,
    predicate,
    source_text,
    content = 'claims',
    content_rowid = 'rowid'
);

CREATE TRIGGER claims_fts_insert AFTER INSERT ON claims BEGIN
    INSERT INTO claims_fts (rowid, claim_text, normalized_claim, subject_original,
        subject_canonical, outcome, predicate, source_text)
    VALUES (new.rowid, new.claim_text, new.normalized_claim, new.subject_original,
        new.subject_canonical, new.outcome, new.predicate, new.source_text);
END;

CREATE TRIGGER claims_fts_delete AFTER DELETE ON claims BEGIN
    INSERT INTO claims_fts (claims_fts, rowid, claim_text, normalized_claim, subject_original,
        subject_canonical, outcome, predicate, source_text)
    VALUES ('delete', old.rowid, old.claim_text, old.normalized_claim, old.subject_original,
        old.subject_canonical, old.outcome, old.predicate, old.source_text);
END;

CREATE TRIGGER claims_fts_update AFTER UPDATE ON claims BEGIN
    INSERT INTO claims_fts (claims_fts, rowid, claim_text, normalized_claim, subject_original,
        subject_canonical, outcome, predicate, source_text)
    VALUES ('delete', old.rowid, old.claim_text, old.normalized_claim, old.subject_original,
        old.subject_canonical, old.outcome, old.predicate, old.source_text);
    INSERT INTO claims_fts (rowid, claim_text, normalized_claim, subject_original,
        subject_canonical, outcome, predicate, source_text)
    VALUES (new.rowid, new.claim_text, new.normalized_claim, new.subject_original,
        new.subject_canonical, new.outcome, new.predicate, new.source_text);
END;

-- Index the claims that an earlier schema version stored.
INSERT INTO claims_fts (claims_fts) VALUES ('rebuild');

CREATE TABLE query_propositions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    domain TEXT,
    subject TEXT NOT NULL,
    relationship TEXT NOT NULL,
    measurement TEXT,
    comparator TEXT,
    expected_direction TEXT,
    dataset TEXT,
    system TEXT,
    population TEXT,
    parse_notes TEXT NOT NULL           -- JSON list of the parse rules that fired
);

CREATE TABLE stance_assessments (
    query_id TEXT NOT NULL REFERENCES query_propositions (id),
    claim_id TEXT NOT NULL REFERENCES claims (id),
    stance TEXT NOT NULL,
    comparability TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (query_id, claim_id)
);

CREATE TABLE dossiers (
    id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL REFERENCES query_propositions (id),
    created_at TEXT NOT NULL,
    corpus_scope TEXT NOT NULL,         -- JSON
    counts TEXT NOT NULL                -- JSON
);
