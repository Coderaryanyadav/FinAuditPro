"""Application DTOs for FinAuditPro Local AI Subsystem and Copilot."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.ai_entities import AICopilotTaskTypeEnum
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


class AICopilotRequestDTO(BaseModel):
    """DTO for triggering a specific AI Copilot capability."""

    model_config = ConfigDict(frozen=False)

    engagement_id: str = Field(...)
    task_type: AICopilotTaskTypeEnum = Field(default=AICopilotTaskTypeEnum.GENERAL_QA)
    prompt: str = Field(default="")
    audit_area: str | None = Field(default=None)
    target_object_id: str | None = Field(
        default=None, description="Optional ID of WP, Evidence, Finding, or Voucher"
    )
    user_id: str = Field(default="Senior Auditor")


class AICopilotDecisionDTO(BaseModel):
    """DTO for explicit human auditor acceptance or rejection of an AI Copilot response."""

    model_config = ConfigDict(frozen=False)

    run_id: str = Field(...)
    decision: str = Field(..., description="'ACCEPTED' or 'REJECTED'")
    user_id: str = Field(default="Auditor")
    decision_notes: str | None = Field(default=None)


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
