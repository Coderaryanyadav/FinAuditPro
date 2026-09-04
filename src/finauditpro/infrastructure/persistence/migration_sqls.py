"""SQL definitions for migrations 006 and 007."""

MIGRATION_006_SQL = """
CREATE TABLE IF NOT EXISTS working_papers (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    index_reference TEXT NOT NULL,
    title TEXT NOT NULL,
    area TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    conclusion TEXT NOT NULL DEFAULT '',
    preparer_id TEXT NOT NULL,
    reviewer_id TEXT,
    content_hash TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    is_locked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS working_paper_sections (
    id TEXT PRIMARY KEY,
    working_paper_id TEXT NOT NULL,
    section_order INTEGER NOT NULL DEFAULT 1,
    title TEXT NOT NULL,
    content_markdown TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(working_paper_id) REFERENCES working_papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS working_paper_links (
    id TEXT PRIMARY KEY,
    working_paper_id TEXT NOT NULL,
    link_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(working_paper_id) REFERENCES working_papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_notes (
    id TEXT PRIMARY KEY,
    working_paper_id TEXT NOT NULL,
    section_id TEXT,
    raised_by TEXT NOT NULL,
    note_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    response_text TEXT,
    responded_by TEXT,
    cleared_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(working_paper_id) REFERENCES working_papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sign_offs (
    id TEXT PRIMARY KEY,
    working_paper_id TEXT NOT NULL,
    level TEXT NOT NULL,
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    entry_hash TEXT,
    note TEXT,
    disclaimer_notice TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(working_paper_id) REFERENCES working_papers(id) ON DELETE CASCADE
);
"""

MIGRATION_007_SQL = """
CREATE TABLE IF NOT EXISTS report_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    report_type TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    section_structure_json TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL,
    jurisdiction TEXT,
    effective_from TEXT NOT NULL,
    verified_statutory INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    template_id TEXT NOT NULL,
    template_version TEXT NOT NULL DEFAULT '1.0',
    title TEXT NOT NULL,
    report_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    data_as_of TEXT NOT NULL,
    content_model_json TEXT NOT NULL DEFAULT '{}',
    content_hash TEXT NOT NULL,
    generated_by TEXT NOT NULL,
    reviewed_by TEXT,
    approved_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(template_id) REFERENCES report_templates(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS report_artifacts (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    format TEXT NOT NULL,
    stored_document_id TEXT,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(report_id) REFERENCES reports(id) ON DELETE CASCADE
);
"""

MIGRATION_008_SQL = """
CREATE TABLE IF NOT EXISTS engagement_archives (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    archive_path TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    sealed_content_hash TEXT NOT NULL,
    is_encrypted INTEGER NOT NULL DEFAULT 0,
    report_date TEXT NOT NULL,
    assembly_deadline TEXT NOT NULL,
    retain_until TEXT NOT NULL,
    sealed_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS retention_configs (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL DEFAULT '1.0',
    assembly_period_days INTEGER NOT NULL DEFAULT 60,
    retention_period_years INTEGER NOT NULL DEFAULT 7,
    source TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    verified_statutory INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS archive_reopen_records (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    reopened_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    prior_archive_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(prior_archive_id) REFERENCES engagement_archives(id) ON DELETE RESTRICT
);
"""

MIGRATION_009_SQL = """
CREATE TABLE IF NOT EXISTS roll_forward_records (
    id TEXT PRIMARY KEY,
    new_engagement_id TEXT NOT NULL,
    source_engagement_id TEXT NOT NULL,
    source_fy TEXT NOT NULL,
    items_carried_json TEXT NOT NULL DEFAULT '[]',
    performed_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(new_engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(source_engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS opening_balance_links (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    source_engagement_id TEXT NOT NULL,
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    opening_dr_paise INTEGER NOT NULL DEFAULT 0,
    opening_cr_paise INTEGER NOT NULL DEFAULT 0,
    prior_closing_dr_paise INTEGER NOT NULL DEFAULT 0,
    prior_closing_cr_paise INTEGER NOT NULL DEFAULT 0,
    is_tied_out INTEGER NOT NULL DEFAULT 0,
    is_verified_by_auditor INTEGER NOT NULL DEFAULT 0,
    verified_at TEXT,
    verified_by TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(source_engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
"""

MIGRATION_011_SQL = """
CREATE TABLE IF NOT EXISTS account_mappings (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    schedule_iii_category TEXT NOT NULL DEFAULT '',
    schedule_iii_line_item TEXT NOT NULL DEFAULT '',
    lead_schedule_ref TEXT NOT NULL DEFAULT 'WP-MISC',
    account_type TEXT NOT NULL DEFAULT 'Asset',
    status TEXT NOT NULL DEFAULT 'Unmapped',
    is_material INTEGER NOT NULL DEFAULT 1,
    is_new INTEGER NOT NULL DEFAULT 0,
    mapped_by TEXT NOT NULL DEFAULT 'Auditor',
    mapped_at TEXT NOT NULL,
    updated_by TEXT,
    updated_at TEXT,
    notes TEXT,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, account_code)
);
CREATE INDEX IF NOT EXISTS idx_acc_map_eng ON account_mappings(engagement_id, status);

CREATE TABLE IF NOT EXISTS account_mapping_history (
    id TEXT PRIMARY KEY,
    mapping_id TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    previous_category TEXT,
    previous_line_item TEXT,
    new_category TEXT NOT NULL,
    new_line_item TEXT NOT NULL,
    reason TEXT,
    FOREIGN KEY(mapping_id) REFERENCES account_mappings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_journal_entries (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    aje_number TEXT NOT NULL,
    entry_date TEXT NOT NULL,
    aje_type TEXT NOT NULL DEFAULT 'Management Accepted',
    status TEXT NOT NULL DEFAULT 'Draft',
    title TEXT NOT NULL,
    narration TEXT NOT NULL,
    reason TEXT NOT NULL,
    working_paper_ref TEXT,
    total_debit_paise INTEGER NOT NULL DEFAULT 0,
    total_credit_paise INTEGER NOT NULL DEFAULT 0,
    prepared_by TEXT NOT NULL,
    prepared_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    reversal_of_entry_id TEXT,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, aje_number)
);
CREATE INDEX IF NOT EXISTS idx_aje_eng_status ON audit_journal_entries(engagement_id, status);

CREATE TABLE IF NOT EXISTS audit_journal_lines (
    id TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    line_no INTEGER NOT NULL,
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    debit_paise INTEGER NOT NULL DEFAULT 0,
    credit_paise INTEGER NOT NULL DEFAULT 0,
    lead_schedule_ref TEXT,
    narration TEXT,
    FOREIGN KEY(entry_id) REFERENCES audit_journal_entries(id) ON DELETE CASCADE
);
"""

MIGRATION_012_SQL = """
CREATE TABLE IF NOT EXISTS audit_sample_items (
    id TEXT PRIMARY KEY,
    procedure_id TEXT NOT NULL,
    sample_plan_id TEXT,
    item_identifier TEXT NOT NULL,
    account_code TEXT,
    expected_value_paise INTEGER NOT NULL DEFAULT 0,
    actual_value_paise INTEGER NOT NULL DEFAULT 0,
    difference_paise INTEGER NOT NULL DEFAULT 0,
    test_result TEXT NOT NULL DEFAULT 'PASS',
    explanation TEXT NOT NULL DEFAULT '',
    evidence_ref TEXT,
    tested_by TEXT NOT NULL DEFAULT 'Auditor',
    created_at TEXT NOT NULL,
    FOREIGN KEY(procedure_id) REFERENCES audit_procedures(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sample_proc ON audit_sample_items(procedure_id);

CREATE TABLE IF NOT EXISTS audit_exceptions (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    procedure_id TEXT NOT NULL,
    sample_item_id TEXT,
    exception_code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_paise INTEGER NOT NULL DEFAULT 0,
    root_cause TEXT NOT NULL DEFAULT '',
    management_response TEXT NOT NULL DEFAULT '',
    is_resolved INTEGER NOT NULL DEFAULT 0,
    resolution TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Open',
    evidence_id TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY(procedure_id) REFERENCES audit_procedures(id) ON DELETE CASCADE,
    FOREIGN KEY(sample_item_id) REFERENCES audit_sample_items(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_exc_eng_status ON audit_exceptions(engagement_id, status);

CREATE TABLE IF NOT EXISTS audit_misstatements (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    exception_id TEXT,
    procedure_id TEXT,
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL DEFAULT '',
    schedule_iii_category TEXT NOT NULL DEFAULT '',
    misstatement_type TEXT NOT NULL DEFAULT 'Factual',
    status TEXT NOT NULL DEFAULT 'Uncorrected',
    amount_paise INTEGER NOT NULL DEFAULT 0,
    is_corrected INTEGER NOT NULL DEFAULT 0,
    linked_aje_id TEXT,
    linked_aje_number TEXT,
    rationale TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT 'Auditor',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_misst_eng_status ON audit_misstatements(engagement_id, status);
"""
