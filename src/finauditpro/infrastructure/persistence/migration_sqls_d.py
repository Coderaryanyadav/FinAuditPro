"""SQL definitions for Phase D migrations (014 and beyond)."""

MIGRATION_014_SQL = """
CREATE TABLE IF NOT EXISTS going_concern_assessments (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    assessment_period_months INTEGER NOT NULL DEFAULT 12,
    has_operating_losses INTEGER NOT NULL DEFAULT 0,
    has_negative_operating_cashflow INTEGER NOT NULL DEFAULT 0,
    has_negative_net_worth INTEGER NOT NULL DEFAULT 0,
    has_covenant_breaches INTEGER NOT NULL DEFAULT 0,
    has_delayed_statutory_dues INTEGER NOT NULL DEFAULT 0,
    has_debt_maturity_unfunded INTEGER NOT NULL DEFAULT 0,
    current_ratio REAL NOT NULL DEFAULT 1.0,
    debt_equity_ratio REAL NOT NULL DEFAULT 0.0,
    solvency_risk_level TEXT NOT NULL DEFAULT 'Low / Normal Operating Cycle',
    material_uncertainty_identified INTEGER NOT NULL DEFAULT 0,
    mitigations_json TEXT NOT NULL DEFAULT '[]',
    audit_conclusion TEXT NOT NULL,
    conclusion_rationale TEXT NOT NULL DEFAULT '',
    preparer TEXT NOT NULL DEFAULT 'Senior Auditor',
    reviewer TEXT,
    partner_signoff INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_gc_eng ON going_concern_assessments(engagement_id);

CREATE TABLE IF NOT EXISTS mrl_records (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    mrl_number TEXT NOT NULL,
    financial_year TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft Representation Letter',
    requested_date TEXT NOT NULL,
    signed_date TEXT,
    signatory_name TEXT,
    signatory_designation TEXT,
    clauses_json TEXT NOT NULL DEFAULT '[]',
    is_chronologically_valid INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, mrl_number)
);
CREATE INDEX IF NOT EXISTS idx_mrl_eng ON mrl_records(engagement_id);

CREATE TABLE IF NOT EXISTS subsequent_events (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    estimated_amount_paise INTEGER NOT NULL DEFAULT 0,
    accounting_treatment TEXT NOT NULL,
    is_adjusted_in_fs INTEGER NOT NULL DEFAULT 0,
    is_disclosed_in_notes INTEGER NOT NULL DEFAULT 0,
    working_paper_ref TEXT,
    procedure_applied TEXT NOT NULL,
    auditor_conclusion TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_subseq_eng ON subsequent_events(engagement_id);

CREATE TABLE IF NOT EXISTS final_analytical_reviews (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    ratio_lines_json TEXT NOT NULL DEFAULT '[]',
    has_unexplained_significant_variances INTEGER NOT NULL DEFAULT 0,
    overall_consistency_conclusion TEXT NOT NULL,
    completed_by TEXT NOT NULL DEFAULT 'Senior Auditor',
    reviewed_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_far_eng ON final_analytical_reviews(engagement_id);

CREATE TABLE IF NOT EXISTS completion_checklist_items (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_applicable INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'Not Started',
    supporting_ref TEXT,
    reviewer TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_cci_eng_cat ON completion_checklist_items(engagement_id, category);

CREATE TABLE IF NOT EXISTS related_party_completions (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL UNIQUE,
    register_reviewed INTEGER NOT NULL DEFAULT 1,
    undisclosed_transactions_identified INTEGER NOT NULL DEFAULT 0,
    arms_length_verified INTEGER NOT NULL DEFAULT 1,
    schedule_iii_disclosed INTEGER NOT NULL DEFAULT 1,
    auditor_conclusion TEXT NOT NULL,
    reviewer TEXT,
    is_completed INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sa240_completions (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL UNIQUE,
    management_override_tested INTEGER NOT NULL DEFAULT 1,
    journal_entry_testing_completed INTEGER NOT NULL DEFAULT 1,
    revenue_recognition_presumption_addressed INTEGER NOT NULL DEFAULT 1,
    risk_indicators_identified INTEGER NOT NULL DEFAULT 0,
    auditor_conclusion TEXT NOT NULL,
    reviewer TEXT,
    is_completed INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);
"""
