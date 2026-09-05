"""Data transfer objects for Phase F continuous audit, intelligence, and data quality services."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DataQualityRunRequest:
    engagement_id: str
    dataset_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    as_of_date: date | None = None


@dataclass
class DataQualityIssueDto:
    issue_id: str
    engagement_id: str
    dataset_id: str | None
    issue_type: str
    severity: str
    source: str
    description: str
    affected_records: list[str]
    detected_at: str
    resolution: str | None = None
    resolved_by: str | None = None
    resolved_at: str | None = None


@dataclass
class DataQualityRunResultDto:
    engagement_id: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues: list[DataQualityIssueDto] = field(default_factory=list)


@dataclass
class ContinuousMonitoringRunRequest:
    engagement_id: str
    dataset_id: str | None = None
    period_end_date: date | None = None
    approval_threshold_paise: int = 10_00_00_00  # ₹1 Lakh
    high_value_threshold_paise: int = 50_00_00_00  # ₹50 Lakhs


@dataclass
class RiskFactorContributionDto:
    factor_name: str
    score_contribution: float
    description: str


@dataclass
class ContinuousAlertDto:
    alert_id: str
    engagement_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    source: str
    risk_score: float
    risk_factors: list[RiskFactorContributionDto]
    affected_data: dict[str, Any]
    status: str
    assigned_user: str | None
    dedup_hash: str
    suppressed: bool
    detected_at: str
    model_rule_version: str = "v1.0"


@dataclass
class ContinuousMonitoringSummaryDto:
    engagement_id: str
    transactions_monitored: int
    alerts_generated: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    suppressed_alerts: int
    open_investigations: int
    confirmed_exceptions: int
    alerts: list[ContinuousAlertDto] = field(default_factory=list)


@dataclass
class AssignAlertRequest:
    alert_id: str
    assigned_user: str


@dataclass
class UpdateInvestigationRequest:
    alert_id: str
    auditor_id: str
    status: str = "INVESTIGATING"
    explanation: str = ""
    management_response: str = ""
    conclusion: str = ""
    outcome: str = "Needs Investigation"
    evidence_links: list[str] = field(default_factory=list)
    working_paper_ids: list[str] = field(default_factory=list)
    procedure_ids: list[str] = field(default_factory=list)
    exception_ids: list[str] = field(default_factory=list)
    misstatement_ids: list[str] = field(default_factory=list)


@dataclass
class AlertInvestigationDto:
    investigation_id: str
    alert_id: str
    engagement_id: str
    auditor_id: str
    status: str
    explanation: str
    management_response: str
    conclusion: str
    outcome: str
    evidence_links: list[str]
    working_paper_ids: list[str]
    procedure_ids: list[str]
    exception_ids: list[str]
    misstatement_ids: list[str]
    created_at: str
    updated_at: str


@dataclass
class RecordFeedbackRequest:
    alert_id: str
    auditor_id: str
    was_useful: bool
    is_false_positive: bool
    is_actual_exception: bool
    is_misstatement: bool
    procedure_created: bool
    comments: str = ""


@dataclass
class ContinuousAuditDashboardDto:
    engagement_id: str
    transactions_monitored: int
    alerts_generated: int
    high_risk_signals: int
    open_investigations: int
    confirmed_exceptions: int
    potential_misstatements: int
    control_violations: int
    tax_anomalies: int
    period_end_anomalies: int
    data_quality_issues_count: int
    materiality_exposure: dict[str, Any] = field(default_factory=dict)
