"""DTOs for Context-Aware Local AI Copilot."""

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict


class CopilotContextDTO(BaseModel):
    """Structured operational context provided to the AI Copilot."""

    model_config = ConfigDict(frozen=True)

    practice: str = "FinAuditPro Practice Operating System"
    firm: str | None = None
    firm_id: str | None = None
    client: str | None = None
    client_id: str | None = None
    financial_year: str = "FY 2025-26"
    engagement: str | None = None
    engagement_id: str | None = None
    current_view: str = "Command Center"
    selected_document: str | None = None
    selected_document_id: str | None = None
    selected_page: int | None = None
    selected_transaction: str | None = None
    selected_workpaper: str | None = None
    selected_workpaper_id: str | None = None
    selected_task: str | None = None
    selected_task_id: str | None = None
    selected_finding: str | None = None
    selected_finding_id: str | None = None
    user_role: str = "Auditor"


@dataclass(frozen=True)
class CopilotResponseDTO:
    """Structured AI Copilot response payload."""

    query: str
    response_text: str
    evidence_citations: list[dict[str, Any]] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    reasoning_summary: str = ""
    is_advisory_only: bool = True
    context_used: dict[str, Any] | None = None
    security_boundary_passed: bool = True
