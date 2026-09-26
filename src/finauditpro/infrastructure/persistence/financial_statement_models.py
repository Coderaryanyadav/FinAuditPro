"""SQLAlchemy ORM models for Phase C: Financial Statements, Notes, CARO 2020, and Tax Audit (Form 3CD)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.models import Base


class FinancialStatementPackageModel(Base):
    __tablename__ = "financial_statement_packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft V1")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft", index=True)
    balance_sheet_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    profit_loss_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    cash_flow_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    changes_in_equity_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    is_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class FinancialStatementNoteModel(Base):
    __tablename__ = "financial_statement_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    package_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("financial_statement_packages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    note_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    fs_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Mapped TB Accounts"
    )
    disclosure_classification: Mapped[str] = mapped_column(
        String(50), nullable=False, default="AUTOMATIC"
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    narrative: Mapped[str] = mapped_column(Text, nullable=False, default="")
    prepared_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class AccountingPolicyModel(Base):
    __tablename__ = "accounting_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    policy_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    applicable_standard: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_text: Mapped[str] = mapped_column(Text, nullable=False)
    changes_text: Mapped[str] = mapped_column(Text, nullable=False, default="No changes")
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Approved")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class CAROWorkpaperModel(Base):
    __tablename__ = "caro_workpapers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    clause_title: Mapped[str] = mapped_column(String(255), nullable=False)
    applicability: Mapped[str] = mapped_column(String(50), nullable=False, default="Applicable")
    applicability_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    procedure_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    finding_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    management_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conclusion_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    report_answer: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Unqualified / Favorable"
    )
    preparer: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class TaxAuditCheckModel(Base):
    __tablename__ = "tax_audit_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_source: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_logic: Mapped[str] = mapped_column(Text, nullable=False)
    system_result: Mapped[str] = mapped_column(String(50), nullable=False, default="Compliant")
    auditor_conclusion: Mapped[str] = mapped_column(String(50), nullable=False, default="Compliant")
    exception_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exception_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    evidence_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
