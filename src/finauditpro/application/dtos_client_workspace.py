"""Data Transfer Objects for Unified Client Workspace."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ClientHeaderDTO:
    """Header information for a specific client entity and its active engagement."""

    client_id: str
    client_name: str
    entity_type: str
    pan: str | None
    gstin: str | None
    registered_address: str | None
    industry: str | None
    contact_person: str | None
    contact_email: str | None
    active_fy: str = "—"
    active_engagement_id: str | None = None
    engagement_status: str = "No Active Engagement"


@dataclass
class ClientWorkItemDTO:
    """An audit task, finding, risk, or review note belonging to the client."""

    id: str
    item_type: str  # "FINDING", "RISK", "REVIEW_NOTE", "TASK"
    title: str
    description: str
    status: str
    severity_risk: str  # "HIGH", "MEDIUM", "LOW", "NORMAL"
    financial_year: str
    engagement_id: str


@dataclass
class ClientEngagementSummaryDTO:
    """Summary of an engagement financial year for the client."""

    id: str
    financial_year: str
    audit_type: str
    status: str
    created_at: datetime
    lead_id: str | None = None


@dataclass
class ClientWorkspaceSummaryDTO:
    """Aggregated payload for the single-pane Client Workspace."""

    header: ClientHeaderDTO
    total_documents: int = 0
    storage_size_bytes: int = 0
    total_pbc_requested: int = 0
    total_pbc_received: int = 0
    pending_pbc_count: int = 0
    open_findings_count: int = 0
    open_review_notes_count: int = 0
    reconciliation_mismatches_count: int = 0
    compliance_status: str = "Compliant"
    engagements: list[ClientEngagementSummaryDTO] = field(default_factory=list)
    work_items: list[ClientWorkItemDTO] = field(default_factory=list)
    recent_activities: list[dict[str, Any]] = field(default_factory=list)
