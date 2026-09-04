"""SQLAlchemy ORM models for Account Mapping, Mapping History, and Audit Adjusting Journal Entries (AJE)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.database import Base


class AccountMappingModel(Base):
    __tablename__ = "account_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schedule_iii_category: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", index=True
    )
    schedule_iii_line_item: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", index=True
    )
    lead_schedule_ref: Mapped[str] = mapped_column(
        String(50), nullable=False, default="WP-MISC", index=True
    )
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Asset")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Unmapped", index=True)
    is_material: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mapped_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    mapped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    history_records: Mapped[list["AccountMappingHistoryModel"]] = relationship(
        "AccountMappingHistoryModel", back_populates="mapping", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("engagement_id", "account_code", name="uq_eng_account_code"),
    )


class AccountMappingHistoryModel(Base):
    __tablename__ = "account_mapping_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mapping_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("account_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    previous_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_line_item: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_category: Mapped[str] = mapped_column(String(255), nullable=False)
    new_line_item: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    mapping: Mapped["AccountMappingModel"] = relationship(
        "AccountMappingModel", back_populates="history_records"
    )


class AuditJournalEntryModel(Base):
    __tablename__ = "audit_journal_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    aje_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entry_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    aje_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Management Accepted", index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft", index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    working_paper_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_debit_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_credit_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prepared_by: Mapped[str] = mapped_column(String(255), nullable=False)
    prepared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversal_of_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    lines: Mapped[list["AuditJournalLineModel"]] = relationship(
        "AuditJournalLineModel",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="AuditJournalLineModel.line_no",
    )

    __table_args__ = (UniqueConstraint("engagement_id", "aje_number", name="uq_eng_aje_number"),)


class AuditJournalLineModel(Base):
    __tablename__ = "audit_journal_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entry_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audit_journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    account_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    debit_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credit_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lead_schedule_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)

    entry: Mapped["AuditJournalEntryModel"] = relationship(
        "AuditJournalEntryModel", back_populates="lines"
    )
