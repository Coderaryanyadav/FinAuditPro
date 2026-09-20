"""Performance optimization indexes migration (Migration 018)."""

import sqlite3


def migration_018_fn(conn: sqlite3.Connection) -> None:
    """Safe execution of composite index creation for performance optimization."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {row[0] for row in cursor.fetchall()}

    index_statements = [
        ("documents", "CREATE INDEX IF NOT EXISTS idx_documents_eng_cat ON documents(engagement_id, document_category);"),
        ("work_tasks", "CREATE INDEX IF NOT EXISTS idx_work_tasks_eng_status ON work_tasks(engagement_id, status);"),
        ("work_tasks", "CREATE INDEX IF NOT EXISTS idx_work_tasks_cli_status ON work_tasks(client_id, status);"),
        ("client_document_requests", "CREATE INDEX IF NOT EXISTS idx_document_requests_eng_status ON client_document_requests(engagement_id, status);"),
        ("working_papers", "CREATE INDEX IF NOT EXISTS idx_working_papers_eng_area ON working_papers(engagement_id, area);"),
        ("ledger_entries", "CREATE INDEX IF NOT EXISTS idx_ledger_entries_ds_dt_acc ON ledger_entries(dataset_id, entry_date, account_code);"),
        ("bank_transactions", "CREATE INDEX IF NOT EXISTS idx_bank_txns_ds_dt ON bank_transactions(dataset_id, txn_date);"),
        ("findings", "CREATE INDEX IF NOT EXISTS idx_findings_eng_status ON findings(engagement_id, status);"),
        ("audit_findings", "CREATE INDEX IF NOT EXISTS idx_audit_findings_eng_status ON audit_findings(engagement_id, status);"),
    ]

    for tbl, stmt in index_statements:
        if tbl in existing_tables:
            conn.execute(stmt)
