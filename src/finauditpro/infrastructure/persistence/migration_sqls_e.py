"""SQL Migration 015: Audit Reporting & Professional Deliverables (Phase E)."""

MIGRATION_015_SQL = """
CREATE TABLE IF NOT EXISTS audit_report_workpapers (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    reporting_framework TEXT NOT NULL,
    financial_year TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    applicable_companies_act_framework TEXT NOT NULL,
    applicable_auditing_framework TEXT NOT NULL,
    materiality_paise INTEGER NOT NULL DEFAULT 0,
    proposed_opinion TEXT NOT NULL,
    final_opinion TEXT NOT NULL,
    opinion_rationale TEXT NOT NULL,
    basis_of_opinion_json TEXT NOT NULL DEFAULT '[]',
    kam_applicable BOOLEAN NOT NULL DEFAULT 1,
    key_audit_matters_json TEXT NOT NULL DEFAULT '[]',
    emphasis_other_matters_json TEXT NOT NULL DEFAULT '[]',
    caro_applicable BOOLEAN NOT NULL DEFAULT 1,
    caro_report_summary TEXT NOT NULL DEFAULT '',
    tax_audit_applicable BOOLEAN NOT NULL DEFAULT 1,
    tax_audit_summary TEXT NOT NULL DEFAULT '',
    going_concern_conclusion TEXT NOT NULL DEFAULT '',
    subsequent_events_conclusion TEXT NOT NULL DEFAULT '',
    misstatements_summary TEXT NOT NULL DEFAULT '',
    management_rep_status TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Draft',
    version INTEGER NOT NULL DEFAULT 1,
    is_locked BOOLEAN NOT NULL DEFAULT 0,
    preparer_id TEXT NOT NULL,
    reviewer_id TEXT,
    approved_by_partner_id TEXT,
    approved_at TEXT,
    dependency_hash TEXT NOT NULL DEFAULT '',
    udin TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_report_lineage (
    id TEXT PRIMARY KEY,
    report_workpaper_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    reported_value TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    underlying_value TEXT NOT NULL,
    is_reconciled BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(report_workpaper_id) REFERENCES audit_report_workpapers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_report_versions (
    id TEXT PRIMARY KEY,
    report_workpaper_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    dependency_hash TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(report_workpaper_id) REFERENCES audit_report_workpapers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_audit_report_wp_engagement ON audit_report_workpapers(engagement_id);
CREATE INDEX IF NOT EXISTS idx_audit_report_lineage_wp ON audit_report_lineage(report_workpaper_id);
CREATE INDEX IF NOT EXISTS idx_audit_report_versions_wp ON audit_report_versions(report_workpaper_id);
"""
