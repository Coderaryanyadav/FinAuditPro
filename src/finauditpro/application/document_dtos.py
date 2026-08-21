"""Data Transfer Objects (DTOs) for Document Management."""

from datetime import datetime

from pydantic import BaseModel, Field

from finauditpro.domain.document_entities import DocumentCategoryEnum, DocumentStatusEnum


class UploadDocumentDTO(BaseModel):
    engagement_id: str = Field(...)
    file_path: str = Field(...)
    category: DocumentCategoryEnum = DocumentCategoryEnum.GENERAL


class DocumentSearchResultDTO(BaseModel):
    document_id: str
    filename: str
    category: str
    page_number: int
    matched_snippet: str


class DocumentDetailDTO(BaseModel):
    id: str
    engagement_id: str
    filename: str
    original_path: str
    stored_path: str
    content_hash: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    document_category: DocumentCategoryEnum
    status: DocumentStatusEnum
    failure_reason: str | None
    created_at: datetime
    pages: list[dict[str, str | int | bool | float]] = Field(default_factory=list)
