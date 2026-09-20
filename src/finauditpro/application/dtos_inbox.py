"""Data Transfer Objects for Practice Inbox Intake & Approval Workflow."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InboxItemDTO:
    """An item in the unified Practice Inbox (Document, PBC Request, Query, or AI Suggestion)."""

    id: str
    item_type: str  # "DOCUMENT", "PBC_REQUEST", "QUERY", "AI_SUGGESTION"
    title: str
    client_id: str
    client_name: str
    engagement_id: str
    financial_year: str
    received_time: datetime
    detected_category: str
    confidence_score: float  # e.g., 0.96 for 96%
    status: str  # "RECEIVED", "PROCESSING", "CLASSIFIED", "NEEDS_REVIEW", "ACCEPTED", "REJECTED", "LINKED"
    reasoning_evidence: str | None = None
    model_info: str | None = None
    human_approval_state: str = "PENDING"  # "PENDING", "APPROVED", "REJECTED", "OVERRIDDEN"
    target_route: str = "documents"
    file_path: str | None = None
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"

    @property
    def confidence_percentage(self) -> int:
        return int(self.confidence_score * 100)


@dataclass
class InboxFilterDTO:
    """Filter parameters for querying the Practice Inbox."""

    tab: str = "ALL"  # "ALL", "NEEDS_REVIEW", "DOCUMENTS", "REQUESTS", "AI_SUGGESTIONS"
    client_id: str | None = None
    engagement_id: str | None = None
    search_query: str | None = None


@dataclass
class InboxSummaryDTO:
    """Aggregated payload returned by InboxService."""

    total_items: int = 0
    needs_review_count: int = 0
    documents_count: int = 0
    requests_count: int = 0
    ai_suggestions_count: int = 0
    items: list[InboxItemDTO] = field(default_factory=list)
