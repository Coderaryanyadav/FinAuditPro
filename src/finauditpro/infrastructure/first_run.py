"""Application data directory initialization, Matplotlib environment setup, and startup database bootstrap."""

import os
import sqlite3
from pathlib import Path

from finauditpro.infrastructure.persistence import models  # noqa: F401
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


def get_app_data_dir() -> Path:
    """Return root application data directory path in native OS location."""
    import sys

    app_data = os.environ.get("FINAUDITPRO_DATA_DIR")
    if app_data:
        data_dir = Path(app_data)
    else:
        app_name = "FinAuditPro"
        if sys.platform == "darwin":
            data_dir = Path.home() / "Library" / "Application Support" / app_name
        elif sys.platform == "win32":
            app_data_base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
            data_dir = Path(app_data_base) / app_name
        else:
            xdg_data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
            data_dir = Path(xdg_data) / "finauditpro"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def bootstrap_app_data_dirs() -> tuple[Path, Path, Path, Path]:
    """Create root data directories and configure writable MPLCONFIGDIR for Matplotlib."""
    root_dir = get_app_data_dir()
    db_dir = root_dir / "db"
    docs_dir = root_dir / "documents"
    vector_dir = root_dir / "vector_store"
    mpl_dir = root_dir / "matplotlib"

    for d in (root_dir, db_dir, docs_dir, vector_dir, mpl_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Set writable MPLCONFIGDIR for Matplotlib flowables
    os.environ["MPLCONFIGDIR"] = str(mpl_dir)

    return db_dir, docs_dir, vector_dir, mpl_dir


def _ensure_all_schema_columns(conn: sqlite3.Connection) -> None:
    """Safely add any missing columns to existing SQLite tables."""
    cursor = conn.cursor()


    # 1. engagements table
    cursor.execute("PRAGMA table_info(engagements);")
    eng_cols = {row[1] for row in cursor.fetchall()}
    if eng_cols:
        if "prior_engagement_id" not in eng_cols:
            conn.execute("ALTER TABLE engagements ADD COLUMN prior_engagement_id TEXT;")
        if "engagement_lead_id" not in eng_cols:
            conn.execute("ALTER TABLE engagements ADD COLUMN engagement_lead_id TEXT;")
        if "assigned_team_json" not in eng_cols:
            conn.execute("ALTER TABLE engagements ADD COLUMN assigned_team_json TEXT DEFAULT '[]';")

    # 2. evidence_links table
    cursor.execute("PRAGMA table_info(evidence_links);")
    ev_cols = {row[1] for row in cursor.fetchall()}
    if ev_cols:
        if "dataset_id" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN dataset_id TEXT;")
        if "row_index" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN row_index INTEGER;")
        if "bounding_box_json" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN bounding_box_json TEXT;")
        if "procedure_id" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN procedure_id TEXT;")
        if "document_id" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN document_id TEXT;")
        if "target_id" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN target_id TEXT;")
        if "page_number" not in ev_cols:
            conn.execute("ALTER TABLE evidence_links ADD COLUMN page_number INTEGER DEFAULT 1;")


    # 3. audit_findings table
    cursor.execute("PRAGMA table_info(audit_findings);")
    find_cols = {row[1] for row in cursor.fetchall()}
    if find_cols:
        if "is_ai_generated" not in find_cols:
            conn.execute("ALTER TABLE audit_findings ADD COLUMN is_ai_generated INTEGER DEFAULT 0;")
        if "source" not in find_cols:
            conn.execute("ALTER TABLE audit_findings ADD COLUMN source TEXT DEFAULT 'manual';")
        if "prior_engagement_finding_id" not in find_cols:
            conn.execute("ALTER TABLE audit_findings ADD COLUMN prior_engagement_finding_id TEXT;")
        if "procedure_id" not in find_cols:
            conn.execute("ALTER TABLE audit_findings ADD COLUMN procedure_id TEXT;")
        if "risk_id" not in find_cols:
            conn.execute("ALTER TABLE audit_findings ADD COLUMN risk_id TEXT;")

    conn.commit()


def initialize_database(db_file_path: str | Path | None = None) -> DatabaseManager:
    """Initialize SQLite database, apply schema migrations, and return DatabaseManager instance."""
    db_dir, _, _, _ = bootstrap_app_data_dirs()

    if db_file_path is None:
        db_path = db_dir / "finauditpro.db"
    else:
        db_path = Path(db_file_path)

    db_manager = DatabaseManager(str(db_path))
    db_manager.create_tables()

    # Run DB Migrations (1 to 9)
    runner = MigrationRunner(str(db_path))
    runner.run_all(get_all_migrations())

    # Ensure schema column completeness across all tables
    with sqlite3.connect(str(db_path)) as conn:
        _ensure_all_schema_columns(conn)

    # Ensure triggers are applied after migrations
    db_manager._create_audit_triggers()

    return db_manager
