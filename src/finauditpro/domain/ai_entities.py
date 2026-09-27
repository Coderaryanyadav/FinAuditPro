"""Domain entities for AI Copilot, Context Builder, Structured Responses, and Citation Layer."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class AICopilotTaskTypeEnum(StrEnum):
    SUMMARIZE_EVIDENCE = "Summarize Evidence"
    EXPLAIN_EXCEPTIONS = "Explain Exceptions"
    SUMMARIZE_WORKING_PAPERS = "Summarize Working Papers"
    DRAFT_REVIEW_NOTES = "Draft Review Notes"
    SUGGEST_FOLLOW_UP_QUESTIONS = "Suggest Follow-Up Questions (PBC)"
    EXPLAIN_FINANCIAL_ANOMALIES = "Explain Financial Anomalies"
    SEARCH_ENGAGEMENT_DOCUMENTS = "Search Engagement Documents"
    SUGGEST_RELEVANT_PROCEDURES = "Suggest Relevant Procedures"
    GENERAL_QA = "General Audit QA"


class AICitation(DomainBaseModel):
    """Citation referencing a specific document, page, working paper, or ledger voucher."""

    reference_id: str = Field(..., description="Unique ID of cited artifact (e.g. WP-REV-004, EVD-0092, JV-18292)")
    artifact_type: str = Field(default="Document", description="Document, WorkingPaper, Finding, Voucher, Exception")
    filename_or_title: str = Field(default="")
    page_number: int | None = Field(default=None)
    excerpt: str = Field(default="")
    relevance_score: float = Field(default=0.9, ge=0.0, le=1.0)


class AICopilotContext(DomainBaseModel):
    """Rich audit context supplied to local LLM Copilot."""

    firm_name: str = Field(default="Audit Firm")
    client_name: str = Field(default="Client Entity")
    engagement_id: str = Field(...)
    engagement_title: str = Field(default="Statutory Audit")
    financial_year: str = Field(default="2025-26")
    audit_area: str | None = Field(default=None)
    active_risks: list[dict[str, Any]] = Field(default_factory=list)
    active_procedures: list[dict[str, Any]] = Field(default_factory=list)
    active_working_papers: list[dict[str, Any]] = Field(default_factory=list)
    active_evidence: list[dict[str, Any]] = Field(default_factory=list)
    active_findings: list[dict[str, Any]] = Field(default_factory=list)
    active_exceptions: list[dict[str, Any]] = Field(default_factory=list)


class AICopilotResponse(DomainBaseModel):
    """Structured response from local AI Copilot with mandatory visual marker and citations."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    task_type: AICopilotTaskTypeEnum = Field(default=AICopilotTaskTypeEnum.GENERAL_QA)
    is_ai_generated: bool = Field(default=True)
    visual_marker: str = Field(
        default="[AI-GENERATED CONTENT — FOR AUDITOR REVIEW ONLY — REQUIRES PROFESSIONAL SIGN-OFF]"
    )
    content: str = Field(...)
    reasoning_summary: str = Field(default="")
    source_citations: list[AICitation] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    model_id: str = Field(default="local-lmstudio")
    model_version: str = Field(default="1.0.0")
    user_id: str = Field(default="Auditor")
    timestamp: datetime = Field(default_factory=utc_now)
    decision_status: str = Field(default="PENDING_REVIEW")  # PENDING_REVIEW, ACCEPTED, REJECTED
    decided_by: str | None = Field(default=None)
    decided_at: datetime | None = Field(default=None)
    decision_notes: str | None = Field(default=None)

    # Architectural Invariant: Local AI Copilot cannot independently mutate official conclusions
    can_autonomously_modify_audit_record: bool = Field(
        default=False,
        description="Must always be False. AI suggestions require explicit human confirmation.",
    )


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
