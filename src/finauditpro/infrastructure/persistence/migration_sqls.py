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
