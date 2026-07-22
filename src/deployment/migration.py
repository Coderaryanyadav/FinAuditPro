"""
Database & Settings Migration Engine for FinAuditPro.
Applies automatic SQLite database schema migrations and user configuration upgrades.
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Manages SQLite schema version tracking and automatic migrations."""

    @staticmethod
    def migrate(db_path: str = "src/data/finauditpro.db") -> bool:
        """Applies pending schema migrations to SQLite database."""
        if not os.path.exists(db_path):
            logger.info("Database file does not exist yet. Migration skipped.")
            return True

        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()

            # Create schema_version table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("SELECT MAX(version) FROM schema_version")
            row = cur.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            # Migration 1: Enable WAL mode
            if current_version < 1:
                cur.execute("PRAGMA journal_mode=WAL;")
                cur.execute("INSERT INTO schema_version (version) VALUES (1);")
                logger.info("Applied Database Migration 1: WAL mode enabled.")

            # Migration 2: Add audit_id column to findings table if missing
            cur.execute("PRAGMA table_info(findings);")
            columns = [col[1] for col in cur.fetchall()]
            if columns and "audit_id" not in columns:
                cur.execute("ALTER TABLE findings ADD COLUMN audit_id INTEGER REFERENCES audit_projects(id);")
                logger.info("Applied Database Migration 2: Added audit_id column to findings table.")

            # Migration 3: Add audit_id column to working_papers table if missing
            cur.execute("PRAGMA table_info(working_papers);")
            wp_cols = [col[1] for col in cur.fetchall()]
            if wp_cols and "audit_id" not in wp_cols:
                cur.execute("ALTER TABLE working_papers ADD COLUMN audit_id INTEGER REFERENCES audit_projects(id);")
                logger.info("Applied Database Migration 3: Added audit_id column to working_papers table.")

            # Migration 4: Add ocr_confidence column to documents table if missing
            cur.execute("PRAGMA table_info(documents);")
            doc_cols = [col[1] for col in cur.fetchall()]
            if doc_cols and "ocr_confidence" not in doc_cols:
                cur.execute("ALTER TABLE documents ADD COLUMN ocr_confidence FLOAT DEFAULT 98.5;")
                logger.info("Applied Database Migration 4: Added ocr_confidence column to documents table.")

            # Migration 5: Add previous_hash and entry_hash columns to audit_logs table if missing
            cur.execute("PRAGMA table_info(audit_logs);")
            audit_cols = [col[1] for col in cur.fetchall()]
            if audit_cols:
                if "previous_hash" not in audit_cols:
                    cur.execute("ALTER TABLE audit_logs ADD COLUMN previous_hash VARCHAR(64);")
                    logger.info("Applied Database Migration 5: Added previous_hash column to audit_logs table.")
                if "entry_hash" not in audit_cols:
                    cur.execute("ALTER TABLE audit_logs ADD COLUMN entry_hash VARCHAR(64);")
                    logger.info("Applied Database Migration 5: Added entry_hash column to audit_logs table.")

            if current_version < 5:
                cur.execute("INSERT INTO schema_version (version) VALUES (5);")

            con.commit()
            con.close()
            return True
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False
