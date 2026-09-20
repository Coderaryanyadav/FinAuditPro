"""Data Transfer Objects for Practice Command Center Dashboard."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttentionItemDTO:
    """An item requiring CA practice or auditor attention."""

    id: str
    category: str  # e.g., "Overdue PBC", "Open Finding", "Review Note", "GST Mismatch"
    title: str
    description: str
    count: int = 1
    urgency: str = "warning"  # "critical", "warning", "info"
    target_route: str = "dashboard"  # Route key for navigation
    target_id: str | None = None


@dataclass
class ActiveClientSummaryDTO:
    """Summary row for an active client and its current engagement."""

    client_id: str
    client_name: str
    industry: str | None
    engagement_id: str | None
    financial_year: str
    audit_type: str
    status: str
    pending_pbc_count: int = 0
    open_findings_count: int = 0
    risk_level: str = "Normal"  # "Normal", "Medium", "High"


@dataclass
class RecentActivityItemDTO:
    """Log entry representing recent practice/audit event activity."""

    id: str
    event_type: str
    description: str
    timestamp: datetime
    user_name: str
    entity_type: str
    entity_id: str | None = None


@dataclass
class UpcomingDeadlineDTO:
    """An upcoming statutory deadline or engagement milestone."""

    id: str
    title: str
    client_name: str
    due_date: str
    category: str
    status: str = "Pending"


@dataclass
class ClientRequestStatusDTO:
    """PBC Document Request status summary for a client engagement."""

    client_id: str
    client_name: str
    engagement_id: str
    total_requested: int
    total_received: int
    pending_count: int

    @property
    def percentage_received(self) -> int:
        if self.total_requested <= 0:
            return 100
        return int((self.total_received / self.total_requested) * 100)


@dataclass
class ReconciliationExceptionDTO:
    """GST or Trial Balance reconciliation exception summary."""

    id: str
    title: str
    category: str  # e.g. "GSTR-2B Mismatch", "TB Discrepancy"
    mismatch_count: int
    total_discrepancy_amount: float
    engagement_id: str
    client_name: str


@dataclass
class PracticeDashboardSummaryDTO:
    """Complete aggregated practice payload for the Command Center."""

    firm_id: str | None
    firm_name: str
    total_clients: int = 0
    active_engagements: int = 0
    completed_audits: int = 0
    attention_items: list[AttentionItemDTO] = field(default_factory=list)
    active_clients: list[ActiveClientSummaryDTO] = field(default_factory=list)
    recent_activities: list[RecentActivityItemDTO] = field(default_factory=list)
    upcoming_deadlines: list[UpcomingDeadlineDTO] = field(default_factory=list)
    client_request_statuses: list[ClientRequestStatusDTO] = field(default_factory=list)
    reconciliation_exceptions: list[ReconciliationExceptionDTO] = field(default_factory=list)
