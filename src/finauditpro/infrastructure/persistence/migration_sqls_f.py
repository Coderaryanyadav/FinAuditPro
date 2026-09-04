"""Database schema migrations for Phase F: Continuous Audit, Intelligence & Advanced Assurance."""

MIGRATION_016_SQL = """
CREATE TABLE IF NOT EXISTS data_quality_issues (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    dataset_id TEXT,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_records_json TEXT NOT NULL DEFAULT '[]',
    resolution TEXT,
    resolved_by TEXT,
    resolved_at TEXT,
    detected_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dqi_engagement ON data_quality_issues(engagement_id);
CREATE INDEX IF NOT EXISTS idx_dqi_severity ON data_quality_issues(severity);

CREATE TABLE IF NOT EXISTS continuous_audit_alerts (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL,
    risk_score REAL NOT NULL DEFAULT 0.0,
    risk_factors_json TEXT NOT NULL DEFAULT '[]',
    affected_data_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'NEW',
    assigned_user TEXT,
    dedup_hash TEXT NOT NULL DEFAULT '',
    suppressed INTEGER NOT NULL DEFAULT 0,
    suppression_reason TEXT,
    is_experimental INTEGER NOT NULL DEFAULT 0,
    model_rule_version TEXT NOT NULL DEFAULT 'v1.0',
    detected_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_engagement ON continuous_audit_alerts(engagement_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON continuous_audit_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON continuous_audit_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_dedup ON continuous_audit_alerts(dedup_hash);

CREATE TABLE IF NOT EXISTS alert_investigations (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    engagement_id TEXT NOT NULL,
    auditor_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'INVESTIGATING',
    evidence_links_json TEXT NOT NULL DEFAULT '[]',
    working_paper_ids_json TEXT NOT NULL DEFAULT '[]',
    procedure_ids_json TEXT NOT NULL DEFAULT '[]',
    exception_ids_json TEXT NOT NULL DEFAULT '[]',
    misstatement_ids_json TEXT NOT NULL DEFAULT '[]',
    explanation TEXT NOT NULL DEFAULT '',
    management_response TEXT NOT NULL DEFAULT '',
    conclusion TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT 'Needs Investigation',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(alert_id) REFERENCES continuous_audit_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_investigation_alert ON alert_investigations(alert_id);
CREATE INDEX IF NOT EXISTS idx_investigation_engagement ON alert_investigations(engagement_id);

CREATE TABLE IF NOT EXISTS alert_feedback_records (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    auditor_id TEXT NOT NULL,
    was_useful INTEGER NOT NULL DEFAULT 1,
    is_false_positive INTEGER NOT NULL DEFAULT 0,
    is_actual_exception INTEGER NOT NULL DEFAULT 0,
    is_misstatement INTEGER NOT NULL DEFAULT 0,
    procedure_created INTEGER NOT NULL DEFAULT 0,
    comments TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(alert_id) REFERENCES continuous_audit_alerts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_alert ON alert_feedback_records(alert_id);

CREATE TABLE IF NOT EXISTS continuous_reconciliation_records (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    reconciliation_type TEXT NOT NULL,
    expected_paise INTEGER NOT NULL DEFAULT 0,
    actual_paise INTEGER NOT NULL DEFAULT 0,
    difference_paise INTEGER NOT NULL DEFAULT 0,
    threshold_paise INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'BALANCED',
    details TEXT NOT NULL DEFAULT '',
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recon_engagement ON continuous_reconciliation_records(engagement_id);
"""
