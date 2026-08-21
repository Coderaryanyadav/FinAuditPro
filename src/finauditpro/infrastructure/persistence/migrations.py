"""Hand-rolled forward-only schema migration runner for SQLite."""

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime


class MigrationRunner:
    """Hand-rolled migration runner applying schema versions in transactions."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_migration_table(self) -> None:
        """Create schema_migrations tracking table if not exists."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );
            """)
            conn.commit()

    def get_applied_versions(self) -> set[int]:
        """Get set of already applied migration version numbers."""
        self.init_migration_table()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
            return {row[0] for row in cursor.fetchall()}

    def apply_migration(
        self, version: int, name: str, sql_or_fn: str | Callable[[sqlite3.Connection], None]
    ) -> bool:
        """Apply a single versioned migration in an isolated transaction."""
        applied = self.get_applied_versions()
        if version in applied:
            return False  # Already applied

        with self._get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION;")
                if isinstance(sql_or_fn, str):
                    conn.executescript(sql_or_fn)
                else:
                    sql_or_fn(conn)

                applied_at = datetime.now(UTC).isoformat()
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?);",
                    (version, name, applied_at),
                )
                conn.commit()
                return True
            except Exception as ex:
                conn.rollback()
                raise RuntimeError(f"Migration version {version} ('{name}') failed: {ex}") from ex

    def run_all(
        self, migrations: list[tuple[int, str, str | Callable[[sqlite3.Connection], None]]]
    ) -> int:
        """Run all pending migrations in version order."""
        self.init_migration_table()
        sorted_migrations = sorted(migrations, key=lambda m: m[0])
        applied_count = 0

        for ver, name, fn_or_sql in sorted_migrations:
            if self.apply_migration(ver, name, fn_or_sql):
                applied_count += 1

        return applied_count
