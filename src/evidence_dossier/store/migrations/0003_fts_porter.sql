-- Rebuild the claims index with the porter stemmer, so "factuality" finds "factual"
-- and "augmentation" finds "augmented". The columns and the three triggers stay as in 0002.

DROP TRIGGER claims_fts_insert;
DROP TRIGGER claims_fts_delete;
DROP TRIGGER claims_fts_update;
DROP TABLE claims_fts;

CREATE VIRTUAL TABLE claims_fts USING fts5 (
    claim_text,
    normalized_claim,
    subject_original,
    subject_canonical,
    outcome,
    predicate,
    source_text,
    content = 'claims',
    content_rowid = 'rowid',
    tokenize = 'porter unicode61'
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

INSERT INTO claims_fts (claims_fts) VALUES ('rebuild');
