"""Domain entities and value objects for continuous audit, intelligence, and data quality assurance."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DataQualitySeverityEnum(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class DataQualityTypeEnum(str, Enum):
    MISSING_ACCOUNT = "Missing Account"
    DUPLICATE_TXN = "Duplicate Transaction"
    DUPLICATE_JOURNAL_ID = "Duplicate Journal ID"
    INVALID_DATE = "Invalid Date"
    FUTURE_DATED = "Future Dated Transaction"
    INVALID_ACCOUNT_REF = "Invalid Account Reference"
    UNBALANCED_JOURNAL = "Unbalanced Journal"
    MISSING_DESCRIPTION = "Missing Description"
    MISSING_USER = "Missing User Reference"
    INVALID_PERIOD = "Invalid Accounting Period"
    CROSS_ENGAGEMENT_REF = "Cross-Engagement Reference Leak"
    UNEXPECTED_CURRENCY = "Unexpected Currency"
    INVALID_DEBIT_CREDIT_SIGN = "Invalid Debit/Credit Sign"


@dataclass
class DataQualityIssue:
    issue_id: str
    engagement_id: str
    dataset_id: Optional[str]
    issue_type: DataQualityTypeEnum
    severity: DataQualitySeverityEnum
    source: str
    detected_at: datetime
    affected_records: list[str]
    description: str
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class AlertSeverityEnum(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class AlertStatusEnum(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    ESCALATED = "ESCALATED"


class AlertTypeEnum(str, Enum):
    UNUSUAL_TRANSACTION = "UNUSUAL_TRANSACTION"
    JOURNAL_RISK = "JOURNAL_RISK"
    USER_BEHAVIOR = "USER_BEHAVIOR"
    PERIOD_END_ANOMALY = "PERIOD_END_ANOMALY"
    ACCOUNT_ANOMALY = "ACCOUNT_ANOMALY"
    BENFORD_ANOMALY = "BENFORD_ANOMALY"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"
    SPLIT_TRANSACTION = "SPLIT_TRANSACTION"
    RELATED_PARTY_ANOMALY = "RELATED_PARTY_ANOMALY"
    TAX_ANOMALY = "TAX_ANOMALY"
    CONTROL_VIOLATION = "CONTROL_VIOLATION"
    RECONCILIATION_BREAK = "RECONCILIATION_BREAK"


@dataclass
class RiskFactorContribution:
    factor_name: str
    score_contribution: float
    description: str


@dataclass
class ContinuousAlert:
    alert_id: str
    engagement_id: str
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    title: str
    description: str
    source: str
    detected_at: datetime
    affected_data: dict[str, Any]
    risk_score: float
    risk_factors: list[RiskFactorContribution] = field(default_factory=list)
    status: AlertStatusEnum = AlertStatusEnum.NEW
    assigned_user: Optional[str] = None
    dedup_hash: str = ""
    suppressed: bool = False
    suppression_reason: Optional[str] = None
    is_experimental: bool = False
    model_rule_version: str = "v1.0"


class InvestigationOutcomeEnum(str, Enum):
    VALID_FINDING = "Valid Finding"
    FALSE_POSITIVE = "False Positive"
    NEEDS_INVESTIGATION = "Needs Investigation"
    NOT_APPLICABLE = "Not Applicable"
    ACCEPTED_RISK = "Accepted Risk"


@dataclass
class AlertInvestigation:
    investigation_id: str
    alert_id: str
    engagement_id: str
    auditor_id: str
    status: str
    evidence_links: list[str] = field(default_factory=list)
    working_paper_ids: list[str] = field(default_factory=list)
    procedure_ids: list[str] = field(default_factory=list)
    exception_ids: list[str] = field(default_factory=list)
    misstatement_ids: list[str] = field(default_factory=list)
    explanation: str = ""
    management_response: str = ""
    conclusion: str = ""
    outcome: InvestigationOutcomeEnum = InvestigationOutcomeEnum.NEEDS_INVESTIGATION
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AuditorFeedback:
    feedback_id: str
    alert_id: str
    auditor_id: str
    was_useful: bool
    is_false_positive: bool
    is_actual_exception: bool
    is_misstatement: bool
    procedure_created: bool
    comments: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BenfordAnalysisResult:
    population_count: int
    eligible_count: int
    excluded_count: int
    digit_type: str
    observed_distribution: dict[int, float]
    expected_distribution: dict[int, float]
    chi_square_stat: float
    p_value_approx: float
    deviation_detected: bool
    label: str = "Analytical anomaly indicator"
    interpretation: str = ""
    limitations: str = (
        "Benford analysis is an analytical indicator of potential distribution divergence. "
        "It does not constitute conclusive evidence of irregularity or accounting error."
    )
    auditor_conclusion: Optional[str] = None


@dataclass
class ContinuousReconciliationResult:
    reconciliation_type: str
    expected_paise: int
    actual_paise: int
    difference_paise: int
    threshold_paise: int
    status: str
    details: str
