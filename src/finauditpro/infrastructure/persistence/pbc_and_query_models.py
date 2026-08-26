"""SQLAlchemy ORM models for Client Document Requests (PBC) and Audit Queries."""

import json
from datetime import datetime
from typing import cast

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.database import Base


class ClientDocumentRequestModel(Base):
    __tablename__ = "client_document_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False, default="FY 2025-26")
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Requested", index=True)
    uploaded_doc_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    @property
    def uploaded_doc_ids(self) -> list[str]:
        try:
            return cast(list[str], json.loads(self.uploaded_doc_ids_json))
        except Exception:
            return []

    @uploaded_doc_ids.setter
    def uploaded_doc_ids(self, value: list[str]) -> None:
        self.uploaded_doc_ids_json = json.dumps(value)


class AuditQueryModel(Base):
    __tablename__ = "audit_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    audit_area: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    working_paper_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("working_papers.id", ondelete="SET NULL"), nullable=True, index=True)
    procedure_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("audit_procedures.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to: Mapped[str] = mapped_column(String(255), nullable=False, default="Associate")
    client_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_requested: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft", index=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    escalated_finding_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("audit_findings.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ExternalConfirmationModel(Base):
    __tablename__ = "external_confirmations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    confirmation_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    third_party_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    account_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    book_balance_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    as_of_date: Mapped[str] = mapped_column(String(20), nullable=False, default="2026-03-31")
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft Letter", index=True)
    dispatched_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    response_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confirmed_balance_paise: Mapped[int | None] = mapped_column(nullable=True)
    discrepancy_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    discrepancy_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternative_procedures_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_working_paper_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("working_papers.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

