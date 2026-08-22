#!/usr/bin/env python3
"""Development database reset utility for FinAuditPro.

Safely removes development SQLite database files and re-applies migrations 001..009.
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from finauditpro.infrastructure.first_run import bootstrap_app_data_dirs, initialize_database
from finauditpro.infrastructure.persistence.database import get_default_db_path


def reset_development_database() -> None:
    """Purge and reinitialize the local development database."""
    db_path = get_default_db_path()
    print(f"Target Database: {db_path}")

    # Remove existing db files if present
    for p in [db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")]:
        if p.exists():
            p.unlink()
            print(f"Removed: {p}")

    # Re-bootstrap directories and re-run all migrations
    bootstrap_app_data_dirs()
    db_manager = initialize_database(db_path)
    print(f"Successfully reinitialized clean database with schema migrations 1..9 applied at: {db_manager.db_path}")


if __name__ == "__main__":
    reset_development_database()
