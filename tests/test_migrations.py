import shutil
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from evidence_dossier.store import MIGRATIONS_DIR, apply_migrations


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

    assert first == ["0001_core.sql"]
    assert second == []
    assert _schema(conn) == schema
    assert _versions(conn) == versions
    conn.close()


def test_new_migration_file_gets_applied_without_code_changes(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations)
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn, migrations)
    (migrations / "0002_extra.sql").write_text("CREATE TABLE extra (id TEXT PRIMARY KEY);\n")

    applied = apply_migrations(conn, migrations)

    assert applied == ["0002_extra.sql"]
    assert "extra" in _tables(conn)
    assert _versions(conn) == [("0001_core.sql",), ("0002_extra.sql",)]
    conn.close()


def test_failed_migration_leaves_no_partial_schema(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations)
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn, migrations)
    (migrations / "0002_broken.sql").write_text(
        "CREATE TABLE half (id TEXT PRIMARY KEY);\nCREATE TABLE half (id TEXT PRIMARY KEY);\n"
    )

    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(conn, migrations)

    assert "half" not in _tables(conn)
    assert _versions(conn) == [("0001_core.sql",)]
    conn.close()
