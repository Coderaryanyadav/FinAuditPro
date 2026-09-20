"""DTOs for Work Center task management and work item aggregation."""

from pydantic import BaseModel, ConfigDict


class WorkItemDTO(BaseModel):
    """Unified work item representing a task, compliance action, reconciliation item, request, review note, or audit action."""

    model_config = ConfigDict(frozen=True)

    id: str
    section: str = "Tasks"  # "Tasks", "Compliance", "Reconciliations", "Client Requests", "Review Notes", "Audit Actions"
    title: str
    description: str = ""
    client_id: str | None = None
    client_name: str = "General Practice"
    financial_year: str = "FY 2025-26"
    engagement_id: str | None = None
    engagement_name: str = "N/A"
    assignee: str = "Unassigned"
    created_at: str
    due_at: str | None = "N/A"
    status: str = "TODO"  # TODO, IN_PROGRESS, WAITING_CLIENT, WAITING_REVIEW, COMPLETED, CANCELLED
    priority: str = "MEDIUM"  # URGENT, HIGH, MEDIUM, LOW
    source: str = "MANUAL"  # CLIENT_REQUEST, DOCUMENT, COMPLIANCE, RECONCILIATION, AUDIT, MANUAL, AI_SUGGESTION
    linked_document: str | None = None
    linked_workpaper: str | None = None
    linked_finding: str | None = None
    requires_human_confirmation: bool = False
    is_confirmed: bool = True


class WorkCenterFilterDTO(BaseModel):
    """Filtering criteria for Work Center views."""

    client_id: str | None = None
    financial_year: str | None = None
    engagement_id: str | None = None
    assignee: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None
    search_query: str | None = None
    section: str = "Tasks"


class WorkCenterSummaryDTO(BaseModel):
    """Aggregate metrics summary across Work Center sections."""

    total_tasks: int = 0
    todo_count: int = 0
    in_progress_count: int = 0
    waiting_client_count: int = 0
    waiting_review_count: int = 0
    completed_count: int = 0
    ai_suggestions_pending_confirmation: int = 0

    # Section counts
    tasks_count: int = 0
    compliance_count: int = 0
    reconciliations_count: int = 0
    client_requests_count: int = 0
    review_notes_count: int = 0
    audit_actions_count: int = 0
