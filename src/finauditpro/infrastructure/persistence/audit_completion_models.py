"""SQLAlchemy ORM models for Phase D: Audit Completion & Misstatement Evaluation.

Tables:
- `going_concern_assessments` (SA 570)
- `mrl_records` (SA 580)
- `subsequent_events` (SA 560)
- `final_analytical_reviews` (SA 520)
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.models import Base


class GoingConcernAssessmentModel(Base):
    __tablename__ = "going_concern_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_period_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    has_operating_losses: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_negative_operating_cashflow: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    has_negative_net_worth: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_covenant_breaches: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_delayed_statutory_dues: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_debt_maturity_unfunded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    debt_equity_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    solvency_risk_level: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Low / Normal Operating Cycle"
    )
    material_uncertainty_identified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    mitigations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    audit_conclusion: Mapped[str] = mapped_column(String(255), nullable=False)
    conclusion_rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    preparer: Mapped[str] = mapped_column(String(255), nullable=False, default="Senior Auditor")
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    partner_signoff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class ManagementRepresentationLetterModel(Base):
    __tablename__ = "mrl_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mrl_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Draft Representation Letter", index=True
    )
    requested_date: Mapped[str] = mapped_column(String(20), nullable=False)
    signed_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signatory_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signatory_designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clauses_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_chronologically_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class SubsequentEventModel(Base):
    __tablename__ = "subsequent_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_date: Mapped[str] = mapped_column(String(20), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accounting_treatment: Mapped[str] = mapped_column(Text, nullable=False)
    is_adjusted_in_fs: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_disclosed_in_notes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    working_paper_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    procedure_applied: Mapped[str] = mapped_column(String(255), nullable=False)
    auditor_conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class FinalAnalyticalReviewModel(Base):
    __tablename__ = "final_analytical_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ratio_lines_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    has_unexplained_significant_variances: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    overall_consistency_conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    completed_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Senior Auditor")
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
