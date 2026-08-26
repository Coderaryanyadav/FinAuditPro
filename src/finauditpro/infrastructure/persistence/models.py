"""SQLAlchemy 2.0 ORM database models."""

import json
from datetime import datetime
from typing import Any, cast

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.database import Base


class FirmModel(Base):
    __tablename__ = "firms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    clients: Mapped[list["ClientModel"]] = relationship("ClientModel", back_populates="firm", cascade="all, delete-orphan")
    engagements: Mapped[list["EngagementModel"]] = relationship("EngagementModel", back_populates="firm", cascade="all, delete-orphan")

class ClientModel(Base):
    __tablename__ = "clients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    firm_id: Mapped[str] = mapped_column(String(36), ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Private Limited Company")
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)
    registered_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    firm: Mapped["FirmModel"] = relationship("FirmModel", back_populates="clients")
    engagements: Mapped[list["EngagementModel"]] = relationship("EngagementModel", back_populates="client", cascade="all, delete-orphan")

class EngagementModel(Base):
    __tablename__ = "engagements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    firm_id: Mapped[str] = mapped_column(String(36), ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    audit_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Statutory Audit")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Planning", index=True)
    engagement_lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    prior_engagement_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    assigned_team_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    firm: Mapped["FirmModel"] = relationship("FirmModel", back_populates="engagements")
    client: Mapped["ClientModel"] = relationship("ClientModel", back_populates="engagements")
    documents: Mapped[list["DocumentModel"]] = relationship("DocumentModel", back_populates="engagement", cascade="all, delete-orphan")
    financial_datasets: Mapped[list["FinancialDatasetModel"]] = relationship("FinancialDatasetModel", back_populates="engagement", cascade="all, delete-orphan")

    def __init__(self, **kwargs: Any) -> None:
        team = kwargs.pop("assigned_team", None)
        super().__init__(**kwargs)
        if team is not None:
            self.assigned_team = team


    @property
    def assigned_team(self) -> list[str]:
        try:
            return cast(list[str], json.loads(self.assigned_team_json))
        except Exception:
            return []

    @assigned_team.setter
    def assigned_team(self, value: list[str]) -> None:
        self.assigned_team_json = json.dumps(value)

class DocumentModel(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_category: Mapped[str] = mapped_column(String(100), nullable=False, default="Unclassified")
    machine_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    human_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)
    category_evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    failed_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    engagement: Mapped["EngagementModel"] = relationship("EngagementModel", back_populates="documents")
    pages: Mapped[list["DocumentPageModel"]] = relationship("DocumentPageModel", back_populates="document", cascade="all, delete-orphan")
    tables: Mapped[list["ExtractedTableModel"]] = relationship("ExtractedTableModel", back_populates="document", cascade="all, delete-orphan")
    evidence_links: Mapped[list["EvidenceLinkModel"]] = relationship("EvidenceLinkModel", back_populates="document", cascade="all, delete-orphan")

class DocumentPageModel(Base):
    __tablename__ = "document_pages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text_source: Mapped[str] = mapped_column(String(50), nullable=False, default="native_pdf")
    ocr_applied: Mapped[bool] = mapped_column(nullable=False, default=False)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    ocr_engine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    layout_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="pages")

class ExtractedTableModel(Base):
    __tablename__ = "extracted_tables"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(nullable=False)
    table_index: Mapped[int] = mapped_column(nullable=False, default=0)
    rows_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)
    bbox_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="tables")

DocumentTableModel = ExtractedTableModel

class EvidenceLinkModel(Base):
    __tablename__ = "evidence_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    procedure_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    page_number: Mapped[int | None] = mapped_column(nullable=True, default=1)
    row_index: Mapped[int | None] = mapped_column(nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    bounding_box_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Audit Finding")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    document: Mapped["DocumentModel | None"] = relationship("DocumentModel", back_populates="evidence_links")

class DocumentClassificationRuleModel(Base):
    __tablename__ = "document_classification_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, default="keyword")
    priority: Mapped[int] = mapped_column(nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

class FinancialDatasetModel(Base):
    __tablename__ = "financial_datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False, default="General Ledger")
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(nullable=False, default=0)
    column_mappings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    engagement: Mapped["EngagementModel"] = relationship("EngagementModel", back_populates="financial_datasets")
    ledger_entries: Mapped[list["LedgerEntryModel"]] = relationship("LedgerEntryModel", back_populates="dataset", cascade="all, delete-orphan")

    @property
    def column_mappings(self) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], json.loads(self.column_mappings_json))
        except Exception:
            return {}


class MaterialityAssessmentModel(Base):
    __tablename__ = "materiality_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    benchmark_type: Mapped[str] = mapped_column(String(100), nullable=False)
    benchmark_amount_paise: Mapped[int] = mapped_column(nullable=False)
    benchmark_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified_statutory: Mapped[bool] = mapped_column(nullable=False, default=False)
    overall_percentage: Mapped[float] = mapped_column(nullable=False)
    overall_materiality_paise: Mapped[int] = mapped_column(nullable=False)
    performance_percentage: Mapped[float] = mapped_column(nullable=False)
    performance_materiality_paise: Mapped[int] = mapped_column(nullable=False)
    trivial_percentage: Mapped[float] = mapped_column(nullable=False, default=5.0)
    clearly_trivial_percentage: Mapped[float] = mapped_column(nullable=False, default=5.0)
    clearly_trivial_threshold_paise: Mapped[int] = mapped_column(nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False, default="")
    methodology_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    assessed_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

class AuditRiskModel(Base):
    __tablename__ = "audit_risks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    assertions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    financial_statement_level: Mapped[bool] = mapped_column(nullable=False, default=False)
    inherent_risk: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    control_risk: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    derived_romm: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    is_significant_risk: Mapped[bool] = mapped_column(nullable=False, default=False)
    risk_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Identified")
    prior_engagement_risk_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class AuditProcedureModel(Base):
    __tablename__ = "audit_procedures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    procedure_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    procedure_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Substantive")
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    nature_timing_extent: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_risks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    assertions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    preparer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class ProcedureRiskLinkModel(Base):
    __tablename__ = "procedure_risk_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    procedure_id: Mapped[str] = mapped_column(String(36), ForeignKey("audit_procedures.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_id: Mapped[str] = mapped_column(String(36), ForeignKey("audit_risks.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

class AuditFindingModel(Base):
    __tablename__ = "audit_findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    procedure_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("audit_procedures.id", ondelete="SET NULL"), nullable=True, index=True)
    risk_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("audit_risks.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Substantive Exception")
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="High")
    amount_paise: Mapped[int | None] = mapped_column(nullable=True)
    affected_account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assertion: Mapped[str] = mapped_column(String(100), nullable=False, default="Accuracy")
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open", index=True)
    preparer: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    is_ai_generated: Mapped[bool] = mapped_column(nullable=False, default=False)
    prior_engagement_finding_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

FindingModel = AuditFindingModel

class AuditEvidenceModel(Base):
    __tablename__ = "audit_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("audit_findings.id", ondelete="SET NULL"), nullable=True, index=True)
    procedure_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("audit_procedures.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("financial_datasets.id", ondelete="SET NULL"), nullable=True)
    row_index: Mapped[int | None] = mapped_column(nullable=True)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    bounding_box_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt_or_reference: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    source_row_no: Mapped[int] = mapped_column(nullable=False)
    entry_date: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    voucher_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    voucher_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    account_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    debit_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    credit_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    dataset: Mapped["FinancialDatasetModel"] = relationship("FinancialDatasetModel", back_populates="ledger_entries")

class TrialBalanceLineModel(Base):
    __tablename__ = "trial_balance_lines"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    source_row_no: Mapped[int] = mapped_column(nullable=False)
    account_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    account_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    opening_dr_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    opening_cr_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    debit_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    credit_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    closing_dr_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    closing_cr_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    raw_values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

class BankTransactionModel(Base):
    __tablename__ = "bank_transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    source_row_no: Mapped[int] = mapped_column(nullable=False)
    txn_date: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    value_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    txn_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    debit_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    credit_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    balance_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

class ExceptionItemModel(Base):
    __tablename__ = "exceptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    analytic_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    implicated_rows_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    computed_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class AuditEventModel(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="Associate")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

