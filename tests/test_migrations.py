import shutil
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from evidence_dossier.store import MIGRATIONS_DIR, Store, apply_migrations
from tests.factories import computer_science_paper

CORE_MIGRATIONS = ["0001_core.sql", "0002_query.sql"]


def _schema(conn: sqlite3.Connection) -> list[Any]:
    return conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall()


def _versions(conn: sqlite3.Connection) -> list[Any]:
    return conn.execute("SELECT filename FROM schema_version ORDER BY filename").fetchall()


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def test_applying_migrations_twice_changes_nothing() -> None:
    conn = sqlite3.connect(":memory:")
    first = apply_migrations(conn)
    schema = _schema(conn)
    versions = _versions(conn)

    second = apply_migrations(conn)

    assert first == CORE_MIGRATIONS
    assert second == []
    assert _schema(conn) == schema
    assert _versions(conn) == versions
    conn.close()


def test_new_migration_file_gets_applied_without_code_changes(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations)
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn, migrations)
    (migrations / "0003_extra.sql").write_text("CREATE TABLE extra (id TEXT PRIMARY KEY);\n")

    applied = apply_migrations(conn, migrations)

    assert applied == ["0003_extra.sql"]
    assert "extra" in _tables(conn)
    assert _versions(conn) == [(name,) for name in (*CORE_MIGRATIONS, "0003_extra.sql")]
    conn.close()


def test_failed_migration_leaves_no_partial_schema(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations)
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn, migrations)
    (migrations / "0003_broken.sql").write_text(
        "CREATE TABLE half (id TEXT PRIMARY KEY);\nCREATE TABLE half (id TEXT PRIMARY KEY);\n"
    )

    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(conn, migrations)

    assert "half" not in _tables(conn)
    assert _versions(conn) == [(name,) for name in CORE_MIGRATIONS]
    conn.close()


def _fts_ids(store: Store, term: str) -> list[str]:
    return [claim.id for claim, _rank in store.search_claims(f'"{term}"')]


def test_fts_triggers_keep_the_claim_index_in_sync() -> None:
    paper = computer_science_paper()
    store = Store(":memory:")
    store.add_work(paper.work)
    store.add_source_document(paper.document)
    store.add_section(paper.section)
    store.add_study(paper.study)
    store.add_extraction_run(paper.run)
    assert _fts_ids(store, "retrieval") == []

    store.add_claim(paper.claim)
    assert _fts_ids(store, "retrieval") == [paper.claim.id]

    # No Store method updates or deletes a claim, so the triggers get raw SQL here.
    conn = store._conn
    with conn:
        conn.execute(
            "UPDATE claims SET claim_text = 'Caching cut latency.' WHERE id = ?", (paper.claim.id,)
        )
    assert _fts_ids(store, "caching") == [paper.claim.id]
    assert _fts_ids(store, "lowered") == []
    with conn:
        conn.execute("DELETE FROM claims WHERE id = ?", (paper.claim.id,))
    assert _fts_ids(store, "caching") == []
    assert _fts_ids(store, "retrieval") == []
    store.close()
