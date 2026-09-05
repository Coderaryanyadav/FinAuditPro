"""SQLAlchemy ORM models for Audit Reporting & Professional Deliverables (Phase E)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.database import Base


class AuditReportWorkpaperModel(Base):
    __tablename__ = "audit_report_workpapers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporting_framework: Mapped[str] = mapped_column(String(100), nullable=False)
    financial_year: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    applicable_companies_act_framework: Mapped[str] = mapped_column(String(255), nullable=False)
    applicable_auditing_framework: Mapped[str] = mapped_column(String(255), nullable=False)
    materiality_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposed_opinion: Mapped[str] = mapped_column(String(100), nullable=False)
    final_opinion: Mapped[str] = mapped_column(String(100), nullable=False)
    opinion_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    basis_of_opinion_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    kam_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    key_audit_matters_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    emphasis_other_matters_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    caro_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    caro_report_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tax_audit_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tax_audit_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    going_concern_conclusion: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    subsequent_events_conclusion: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    misstatements_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    management_rep_status: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preparer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by_partner_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dependency_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    udin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class AuditReportLineageModel(Base):
    __tablename__ = "audit_report_lineage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_workpaper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audit_report_workpapers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(150), nullable=False)
    reported_value: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    underlying_value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class AuditReportVersionModel(Base):
    __tablename__ = "audit_report_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_workpaper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audit_report_workpapers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    dependency_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
