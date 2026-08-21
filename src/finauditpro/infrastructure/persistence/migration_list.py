"""Registry of versioned schema migrations for FinAuditPro."""

MIGRATION_001_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
"""

MIGRATION_002_SQL = """
CREATE TABLE IF NOT EXISTS document_tables (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    table_index INTEGER NOT NULL DEFAULT 0,
    rows_json TEXT NOT NULL DEFAULT '[]',
    bbox_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence_links (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    target_type TEXT NOT NULL DEFAULT 'Audit Finding',
    target_id TEXT,
    title TEXT NOT NULL,
    snippet TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    engagement_id UNINDEXED,
    document_id UNINDEXED,
    page_id UNINDEXED,
    page_number UNINDEXED,
    extracted_text,
    tokenize='unicode61'
);
"""

MIGRATION_003_SQL = """
CREATE TABLE IF NOT EXISTS ledger_entries (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    source_row_no INTEGER NOT NULL,
    entry_date TEXT,
    voucher_type TEXT,
    voucher_number TEXT,
    account_code TEXT,
    account_name TEXT,
    debit_paise INTEGER NOT NULL DEFAULT 0,
    credit_paise INTEGER NOT NULL DEFAULT 0,
    narration TEXT,
    reference TEXT,
    created_by_raw TEXT,
    raw_values_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(dataset_id) REFERENCES financial_datasets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ledger_dataset_account ON ledger_entries(dataset_id, account_code);
CREATE INDEX IF NOT EXISTS idx_ledger_dataset_date ON ledger_entries(dataset_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_ledger_dataset_vch ON ledger_entries(dataset_id, voucher_number);

CREATE TABLE IF NOT EXISTS trial_balance_lines (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    source_row_no INTEGER NOT NULL,
    account_code TEXT,
    account_name TEXT NOT NULL,
    account_type TEXT,
    opening_dr_paise INTEGER NOT NULL DEFAULT 0,
    opening_cr_paise INTEGER NOT NULL DEFAULT 0,
    debit_paise INTEGER NOT NULL DEFAULT 0,
    credit_paise INTEGER NOT NULL DEFAULT 0,
    closing_dr_paise INTEGER NOT NULL DEFAULT 0,
    closing_cr_paise INTEGER NOT NULL DEFAULT 0,
    raw_values_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(dataset_id) REFERENCES financial_datasets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bank_transactions (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    source_row_no INTEGER NOT NULL,
    txn_date TEXT,
    value_date TEXT,
    txn_id TEXT,
    description TEXT NOT NULL,
    debit_paise INTEGER NOT NULL DEFAULT 0,
    credit_paise INTEGER NOT NULL DEFAULT 0,
    balance_paise INTEGER NOT NULL DEFAULT 0,
    reference TEXT,
    raw_values_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(dataset_id) REFERENCES financial_datasets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exceptions (
    id TEXT PRIMARY KEY,
    analysis_run_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    analytic_id TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'Medium',
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    implicated_rows_json TEXT NOT NULL DEFAULT '[]',
    computed_evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    reviewer TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(dataset_id) REFERENCES financial_datasets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Substantive Audit Exception',
    severity TEXT NOT NULL DEFAULT 'High',
    amount_paise INTEGER NOT NULL DEFAULT 0,
    affected_account TEXT,
    source TEXT NOT NULL DEFAULT 'Deterministic Analytics Engine',
    ai_generated INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Open',
    preparer TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
"""

MIGRATION_004_SQL = """
CREATE TABLE IF NOT EXISTS materiality_calculations (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    benchmark_type TEXT NOT NULL,
    benchmark_amount_paise INTEGER NOT NULL DEFAULT 0,
    benchmark_source TEXT NOT NULL DEFAULT 'SA 320 Guidance (Editable Suggestion)',
    is_verified_statutory INTEGER NOT NULL DEFAULT 0,
    overall_percentage REAL NOT NULL DEFAULT 1.0,
    overall_materiality_paise INTEGER NOT NULL DEFAULT 0,
    performance_percentage REAL NOT NULL DEFAULT 75.0,
    performance_materiality_paise INTEGER NOT NULL DEFAULT 0,
    trivial_percentage REAL NOT NULL DEFAULT 5.0,
    clearly_trivial_threshold_paise INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    methodology_notes TEXT,
    created_by TEXT NOT NULL DEFAULT 'Lead Auditor',
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_risks (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    risk_code TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    assertions_json TEXT NOT NULL DEFAULT '["Completeness"]',
    inherent_risk TEXT NOT NULL DEFAULT 'Medium',
    control_risk TEXT NOT NULL DEFAULT 'Medium',
    derived_romm TEXT NOT NULL DEFAULT 'Medium',
    is_significant_risk INTEGER NOT NULL DEFAULT 0,
    risk_response TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_procedures (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    procedure_code TEXT NOT NULL,
    objective TEXT NOT NULL,
    procedure_type TEXT NOT NULL DEFAULT 'Substantive Procedure',
    instructions TEXT NOT NULL DEFAULT '',
    evidence_requirement TEXT,
    linked_risks_json TEXT NOT NULL DEFAULT '[]',
    assertions_json TEXT NOT NULL DEFAULT '["Completeness"]',
    status TEXT NOT NULL DEFAULT 'Not Started',
    result_summary TEXT,
    conclusion TEXT,
    preparer TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_findings (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    procedure_id TEXT,
    risk_id TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Substantive Exception',
    severity TEXT NOT NULL DEFAULT 'High',
    amount_paise INTEGER,
    affected_account TEXT,
    assertion TEXT NOT NULL DEFAULT 'Accuracy',
    recommendation TEXT,
    status TEXT NOT NULL DEFAULT 'Open',
    preparer TEXT NOT NULL DEFAULT 'Auditor',
    reviewer TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    ai_generated INTEGER NOT NULL DEFAULT 0,
    prior_engagement_finding_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(procedure_id) REFERENCES audit_procedures(id) ON DELETE SET NULL,
    FOREIGN KEY(risk_id) REFERENCES audit_risks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_evidence (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    finding_id TEXT,
    procedure_id TEXT,
    document_id TEXT,
    dataset_id TEXT,
    row_index INTEGER,
    page_number INTEGER,
    bounding_box_json TEXT,
    title TEXT NOT NULL,
    excerpt_or_reference TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(finding_id) REFERENCES audit_findings(id) ON DELETE SET NULL,
    FOREIGN KEY(procedure_id) REFERENCES audit_procedures(id) ON DELETE SET NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY(dataset_id) REFERENCES financial_datasets(id) ON DELETE SET NULL
);
"""

MIGRATION_005_SQL = """
CREATE TABLE IF NOT EXISTS ai_provider_config (
    id TEXT PRIMARY KEY,
    base_url TEXT NOT NULL DEFAULT 'http://localhost:1234/v1',
    chat_model_id TEXT NOT NULL DEFAULT 'deepseek/deepseek-r1-distill-qwen-14b',
    embedding_model_id TEXT NOT NULL DEFAULT 'text-embedding-nomic-embed-text-v1.5',
    temperature REAL NOT NULL DEFAULT 0.6,
    top_p REAL NOT NULL DEFAULT 0.95,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    char_start INTEGER NOT NULL DEFAULT 0,
    char_end INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding_model_id TEXT,
    dimension INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_runs (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    model_id TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    prompt_version TEXT NOT NULL DEFAULT '1.0',
    retrieved_chunk_ids_json TEXT NOT NULL DEFAULT '[]',
    reasoning_text TEXT,
    response_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Completed',
    created_by TEXT NOT NULL DEFAULT 'Auditor',
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
"""

import sqlite3

from finauditpro.infrastructure.persistence.migration_sqls import (
    MIGRATION_006_SQL,
    MIGRATION_007_SQL,
    MIGRATION_008_SQL,
    MIGRATION_009_SQL,
)


def migration_009_fn(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(engagements);")
    columns = [row[1] for row in cursor.fetchall()]
    if columns and "prior_engagement_id" not in columns:
        conn.execute("ALTER TABLE engagements ADD COLUMN prior_engagement_id TEXT;")
    conn.executescript(MIGRATION_009_SQL)


def get_all_migrations() -> list[tuple[int, str, Any]]:
    return [
        (1, "001_initial_schema", MIGRATION_001_SQL),
        (2, "002_create_document_tables_and_fts", MIGRATION_002_SQL),
        (3, "003_create_financial_tables_and_findings", MIGRATION_003_SQL),
        (4, "004_create_audit_planning_and_unified_findings_tables", MIGRATION_004_SQL),
        (5, "005_create_ai_subsystem_tables", MIGRATION_005_SQL),
        (6, "006_create_working_papers_and_review_tables", MIGRATION_006_SQL),
        (7, "007_create_reporting_tables", MIGRATION_007_SQL),
        (8, "008_create_archival_and_retention_tables", MIGRATION_008_SQL),
        (9, "009_create_roll_forward_tables", migration_009_fn),
    ]
