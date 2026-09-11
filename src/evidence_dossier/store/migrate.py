"""Versioned SQL migrations for the evidence store (ADR 0002).

Each .sql file in the migrations folder runs once, in filename order, and the
schema_version table records it. A new file needs no code change.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def apply_migrations(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply each migration file that schema_version does not list yet, and return their names.

    Each file runs in one transaction together with its schema_version row, so
    a failed file leaves no partial schema. For that reason a migration file
    contains no BEGIN or COMMIT of its own.
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version"
        " (filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    done = {row[0] for row in conn.execute("SELECT filename FROM schema_version")}
    applied: list[str] = []
    for path in sorted(directory.glob("*.sql")):
        if path.name in done:
            continue
        try:
            conn.executescript("BEGIN;\n" + path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_version (filename, applied_at) VALUES (?, ?)",
                (path.name, datetime.now(UTC).isoformat()),
            )
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        applied.append(path.name)
    return applied
