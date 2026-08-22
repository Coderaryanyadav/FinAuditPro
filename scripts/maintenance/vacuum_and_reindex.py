#!/usr/bin/env python3
"""Database maintenance utility for SQLite WAL vacuuming, optimization, and FTS5 re-indexing."""

import sqlite3
import sys
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from finauditpro.infrastructure.persistence.database import get_default_db_path


def optimize_database(db_path: Path | None = None) -> None:
    target_path = db_path or get_default_db_path()
    print(f"Starting database optimization on: {target_path}")

    if not target_path.exists():
        print(f"Error: Target database file does not exist: {target_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(target_path))
    cursor = conn.cursor()

    try:
        print("  • Executing WAL checkpoint...")
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")

        print("  • Re-indexing SQLite tables...")
        cursor.execute("REINDEX;")

        # Re-index FTS5 virtual table if present
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents_fts';"
        )
        if cursor.fetchone():
            print("  • Optimizing FTS5 full-text index...")
            cursor.execute("INSERT INTO documents_fts(documents_fts) VALUES('optimize');")

        print("  • Running incremental vacuum and PRAGMA optimize...")
        cursor.execute("PRAGMA optimize;")
        cursor.execute("VACUUM;")

        conn.commit()
        print("✓ Database optimization completed successfully.")
    except Exception as ex:
        print(f"Error during database optimization: {ex}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    optimize_database()
