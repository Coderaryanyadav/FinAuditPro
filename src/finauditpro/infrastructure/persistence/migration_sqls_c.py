"""SQL definitions for Phase C migrations (013 and beyond)."""

MIGRATION_013_SQL = """
CREATE TABLE IF NOT EXISTS financial_statement_packages (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'Draft V1',
    status TEXT NOT NULL DEFAULT 'Draft',
    balance_sheet_json TEXT NOT NULL DEFAULT '{}',
    profit_loss_json TEXT NOT NULL DEFAULT '{}',
    cash_flow_json TEXT NOT NULL DEFAULT '{}',
    changes_in_equity_json TEXT NOT NULL DEFAULT '{}',
    is_locked INTEGER NOT NULL DEFAULT 0,
    data_hash TEXT NOT NULL DEFAULT '',
    is_stale INTEGER NOT NULL DEFAULT 0,
    created_by TEXT NOT NULL DEFAULT 'Auditor',
    approved_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fsp_eng_status ON financial_statement_packages(engagement_id, status);

CREATE TABLE IF NOT EXISTS financial_statement_notes (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    package_id TEXT,
    note_number TEXT NOT NULL,
    title TEXT NOT NULL,
    fs_reference TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'Mapped TB Accounts',
    disclosure_classification TEXT NOT NULL DEFAULT 'AUTOMATIC',
    amount_paise INTEGER NOT NULL DEFAULT 0,
    details_json TEXT NOT NULL DEFAULT '[]',
    narrative TEXT NOT NULL DEFAULT '',
    prepared_by TEXT NOT NULL DEFAULT 'Auditor',
    reviewed_by TEXT,
    status TEXT NOT NULL DEFAULT 'Draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(package_id) REFERENCES financial_statement_packages(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_fsn_eng_note ON financial_statement_notes(engagement_id, note_number);

CREATE TABLE IF NOT EXISTS accounting_policies (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    policy_code TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    applicable_standard TEXT NOT NULL,
    policy_text TEXT NOT NULL,
    changes_text TEXT NOT NULL DEFAULT 'No changes',
    reviewed_by TEXT,
    status TEXT NOT NULL DEFAULT 'Approved',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pol_eng_code ON accounting_policies(engagement_id, policy_code);

CREATE TABLE IF NOT EXISTS caro_workpapers (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    clause_code TEXT NOT NULL,
    clause_title TEXT NOT NULL,
    applicability TEXT NOT NULL DEFAULT 'Applicable',
    applicability_reason TEXT NOT NULL DEFAULT '',
    question TEXT NOT NULL DEFAULT '',
    procedure_text TEXT NOT NULL DEFAULT '',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    finding_refs_json TEXT NOT NULL DEFAULT '[]',
    management_response TEXT NOT NULL DEFAULT '',
    conclusion_text TEXT NOT NULL DEFAULT '',
    report_answer TEXT NOT NULL DEFAULT 'Unqualified / Favorable',
    preparer TEXT NOT NULL DEFAULT 'Auditor',
    reviewer TEXT,
    status TEXT NOT NULL DEFAULT 'Draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_caro_eng_clause ON caro_workpapers(engagement_id, clause_code);

CREATE TABLE IF NOT EXISTS tax_audit_checks (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    clause_code TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    input_source TEXT NOT NULL,
    rule_logic TEXT NOT NULL,
    system_result TEXT NOT NULL DEFAULT 'Compliant',
    auditor_conclusion TEXT NOT NULL DEFAULT 'Compliant',
    exception_amount_paise INTEGER NOT NULL DEFAULT 0,
    exception_id TEXT,
    evidence_ref TEXT,
    reviewer_notes TEXT,
    reviewer TEXT,
    status TEXT NOT NULL DEFAULT 'Completed',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tac_eng_clause ON tax_audit_checks(engagement_id, clause_code);
"""
