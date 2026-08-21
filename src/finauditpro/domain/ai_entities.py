"""Domain entities for AI Copilot, RAG Citations, and Structured Observations."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class AICitation(DomainBaseModel):
    document_id: str = Field(...)
    filename: str = Field(...)
    page_number: int = Field(..., ge=1)
    excerpt: str = Field(...)
    relevance_score: float = Field(default=0.9, ge=0.0, le=1.0)


class AIStructuredObservation(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(...)
    observation: str = Field(...)
    citations: list[AICitation] = Field(default_factory=list)
    risk_severity: str = Field(default="Medium")
    recommended_procedure: str | None = Field(default=None)
    confidence_score: float = Field(default=0.88, ge=0.0, le=1.0)
    is_ai_generated: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)


class AIChatMessage(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    role: str = Field(..., description="user or assistant or system")
    text_content: str = Field(...)
    citations: list[AICitation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
