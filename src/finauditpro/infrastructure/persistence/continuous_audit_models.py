"""SQLAlchemy ORM models for continuous audit, intelligence, and data quality assurance."""

from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.infrastructure.persistence.models import Base


class DataQualityIssueModel(Base):
    """Represents a detected financial data quality issue."""

    __tablename__ = "data_quality_issues"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(String, nullable=True)
    issue_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_records_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(String, nullable=True)
    detected_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class ContinuousAlertModel(Base):
    """Represents an intelligent continuous audit risk alert or analytical signal."""

    __tablename__ = "continuous_audit_alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_factors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    affected_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String, nullable=False, default="NEW")
    assigned_user: Mapped[str | None] = mapped_column(String, nullable=True)
    dedup_hash: Mapped[str] = mapped_column(String, nullable=False, default="")
    suppressed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suppression_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_experimental: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_rule_version: Mapped[str] = mapped_column(String, nullable=False, default="v1.0")
    detected_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class AlertInvestigationModel(Base):
    """Represents an auditor investigation linked to an automated system alert."""

    __tablename__ = "alert_investigations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String, ForeignKey("continuous_audit_alerts.id", ondelete="CASCADE"), nullable=False)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    auditor_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="INVESTIGATING")
    evidence_links_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    working_paper_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    procedure_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    exception_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    misstatement_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    management_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    outcome: Mapped[str] = mapped_column(String, nullable=False, default="Needs Investigation")
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class AlertFeedbackModel(Base):
    """Represents auditor feedback and false-positive tracking on continuous alerts."""

    __tablename__ = "alert_feedback_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String, ForeignKey("continuous_audit_alerts.id", ondelete="CASCADE"), nullable=False)
    auditor_id: Mapped[str] = mapped_column(String, nullable=False)
    was_useful: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_false_positive: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_actual_exception: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_misstatement: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    procedure_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recorded_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class ContinuousReconciliationRecordModel(Base):
    """Represents historical records of continuous ledger, subledger, and TB balance checks."""

    __tablename__ = "continuous_reconciliation_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    reconciliation_type: Mapped[str] = mapped_column(String, nullable=False)
    expected_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difference_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    threshold_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="BALANCED")
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evaluated_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())
