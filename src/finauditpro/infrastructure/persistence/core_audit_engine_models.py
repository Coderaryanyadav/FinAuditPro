"""SQLAlchemy ORM models for Core Audit Engine: Sample Items, Exceptions, and SA 450 Misstatements."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.models import Base


class AuditSampleItemModel(Base):
    __tablename__ = "audit_sample_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    procedure_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audit_procedures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sample_plan_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    item_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    account_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    expected_value_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_value_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difference_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    test_result: Mapped[str] = mapped_column(String(50), nullable=False, default="PASS")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tested_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class AuditExceptionModel(Base):
    __tablename__ = "audit_exceptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    procedure_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audit_procedures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sample_item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("audit_sample_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    exception_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False, default="")
    management_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open", index=True)
    evidence_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class AuditMisstatementModel(Base):
    __tablename__ = "audit_misstatements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exception_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    procedure_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    account_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    schedule_iii_category: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    misstatement_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Factual")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Uncorrected", index=True
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_corrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    linked_aje_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    linked_aje_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
