"""Domain entities for Document Intelligence, Classification, and Evidence Linking."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finauditpro.domain.clock import utc_now
from finauditpro.domain.exceptions import ValidationError


class DocumentCategoryEnum(StrEnum):
    BANK_STATEMENT = "Bank Statement"
    TAX_RETURN = "Tax Return"
    INVOICE = "Invoice"
    PURCHASE_ORDER = "Purchase Order"
    FINANCIAL_STATEMENT = "Financial Statement"
    BOARD_MINUTES = "Board Minutes"
    AUDIT_REPORT = "Audit Report"
    CONTRACT = "Contract"
    GENERAL = "General"


class DocumentStatusEnum(StrEnum):
    UPLOADED = "Uploaded"
    VALIDATING = "Validating"
    STORED = "Stored"
    EXTRACTING = "Extracting"
    OCR_QUEUED = "OCR Queued"
    OCR_RUNNING = "OCR Running"
    CLASSIFYING = "Classifying"
    INDEXED = "Indexed"
    READY = "Ready"
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"
    QUARANTINED = "Quarantined"
    DELETED = "Deleted"


class TextSourceEnum(StrEnum):
    BORN_DIGITAL = "Born Digital"
    OCR = "OCR"
    MANUAL = "Manual"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class DocumentPage(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str = Field(...)
    page_number: int = Field(..., ge=1)
    extracted_text: str = Field(default="")
    text_source: TextSourceEnum = Field(default=TextSourceEnum.BORN_DIGITAL)
    ocr_applied: bool = Field(default=False)
    confidence_score: float | None = Field(default=1.0, ge=0.0, le=1.0)
    layout_json: str | None = Field(default=None)

    @property
    def ocr_confidence(self) -> float | None:
        return self.confidence_score

    @property
    def text(self) -> str:
        return self.extracted_text


class DocumentTable(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str = Field(...)
    page_number: int = Field(..., ge=1)
    table_index: int = Field(default=0, ge=0)
    rows_json: str = Field(default="[]")
    bbox_json: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class EvidenceLink(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    document_id: str = Field(...)
    page_number: int = Field(default=1, ge=1)
    target_type: str = Field(default="Audit Finding")
    target_id: str | None = Field(default=None)
    title: str = Field(..., min_length=1)
    snippet: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class Document(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    filename: str = Field(..., min_length=1, max_length=255)
    original_path: str = Field(...)
    stored_path: str = Field(...)
    content_hash: str = Field(..., min_length=64, max_length=64)  # SHA-256 hex string
    mime_type: str = Field(default="application/octet-stream")
    file_size_bytes: int = Field(..., ge=0)
    page_count: int = Field(default=0, ge=0)
    document_category: DocumentCategoryEnum = Field(default=DocumentCategoryEnum.GENERAL)
    status: DocumentStatusEnum = Field(default=DocumentStatusEnum.READY)
    failed_stage: str | None = Field(default=None)
    failure_reason: str | None = Field(default=None)
    machine_category: DocumentCategoryEnum | None = Field(default=None)
    category_confidence: float | None = Field(default=None)
    category_evidence: list[str] = Field(default_factory=list)
    human_category: DocumentCategoryEnum | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("filename")
    @classmethod
    def check_filename(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Filename cannot be empty.")
        return v.strip()
