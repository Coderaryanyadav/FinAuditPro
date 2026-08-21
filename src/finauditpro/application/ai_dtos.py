"""Application DTOs for FinAuditPro Local AI Subsystem."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum


class AIFindingSchema(BaseModel):
    """Pydantic schema for structured AI Finding proposals."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: RiskSeverityEnum = Field(default=RiskSeverityEnum.HIGH)
    assertion: AssertionEnum = Field(default=AssertionEnum.ACCURACY)
    affected_account: str | None = Field(default=None)
    recommendation: str | None = Field(default=None)
    cited_chunk_ids: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class DocumentChunkDTO:
    id: str
    engagement_id: str
    document_id: str
    page_number: int
    char_start: int
    char_end: int
    chunk_text: str
    embedding_model_id: str | None = None
    dimension: int | None = None


@dataclass(frozen=True)
class RAGQueryResultDTO:
    query: str
    response_text: str
    reasoning_text: str | None
    retrieved_chunks: list[dict[str, Any]]
    used_embedding_model: bool
    fallback_fts5_used: bool


@dataclass(frozen=True)
class AIRunRecordDTO:
    id: str
    engagement_id: str
    run_kind: str
    model_id: str
    prompt_version: str
    retrieved_chunk_ids: list[str]
    reasoning_text: str | None
    response_text: str
    status: str
    created_at: str
