"""Domain entities and value objects for Client Document Requests (PBC) and Audit Queries."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from finauditpro.domain.clock import utc_now


class DocumentRequestStatusEnum(StrEnum):
    """Lifecycle status for a Provided By Client (PBC) document request."""

    REQUESTED = "Requested"
    PARTIALLY_RECEIVED = "Partially Received"
    RECEIVED = "Received"
    UNDER_REVIEW = "Under Review"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected / Needs Clarification"


class AuditQueryStatusEnum(StrEnum):
    """Lifecycle status for an auditor query raised to client or engagement team."""

    DRAFT = "Draft"
    SENT_TO_CLIENT = "Sent to Client"
    CLIENT_RESPONDED = "Client Responded"
    UNDER_REVIEW = "Under Review"
    RESOLVED = "Resolved"
    ESCALATED_TO_FINDING = "Escalated to Finding"


@dataclass
class DocumentRequest:
    """Client document request tracking entity."""

    id: str
    engagement_id: str
    title: str
    description: str
    period: str = "FY 2025-26"
    contact_name: str | None = None
    contact_email: str | None = None
    due_date: str | None = None
    status: DocumentRequestStatusEnum = DocumentRequestStatusEnum.REQUESTED
    uploaded_doc_ids: list[str] = field(default_factory=list)
    reviewer_notes: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def transition_to(self, target: DocumentRequestStatusEnum) -> None:
        self.status = target
        self.updated_at = utc_now()


@dataclass
class AuditQuery:
    """Audit query entity linking procedures, working papers, and findings."""

    id: str
    engagement_id: str
    query_text: str
    audit_area: str
    working_paper_id: str | None = None
    procedure_id: str | None = None
    assigned_to: str = "Associate"
    client_contact: str | None = None
    evidence_requested: str | None = None
    due_date: str | None = None
    status: AuditQueryStatusEnum = AuditQueryStatusEnum.DRAFT
    response_text: str | None = None
    resolution_notes: str | None = None
    reviewer_id: str | None = None
    escalated_finding_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def transition_to(self, target: AuditQueryStatusEnum) -> None:
        self.status = target
        self.updated_at = utc_now()


# Standard ICAI Statutory PBC Packages
DEFAULT_STATUTORY_PBC_TEMPLATES: list[dict[str, Any]] = [
    {
        "title": "Signed Trial Balance & General Ledger",
        "description": "Full period General Ledger extract in Excel/CSV format along with signed Trial Balance reconciled with books.",
        "period": "Full Year",
    },
    {
        "title": "Bank Statements & Year-End Balance Confirmations",
        "description": "Bank statements for all active current, CC/OD, and deposit accounts with bank confirmation certificates as of March 31.",
        "period": "Full Year + Q4",
    },
    {
        "title": "GSTR-1, GSTR-3B & GSTR-2B Returns & Annual Reconciliation",
        "description": "Monthly filed GST returns, GSTR-2B JSONs, and ITC reconciliation against Purchase Register (Books).",
        "period": "Monthly / Annual",
    },
    {
        "title": "Fixed Asset Register & Physical Verification Report",
        "description": "Schedule of PPE additions, disposals, depreciation schedule (Companies Act Schedule II), and physical verification report.",
        "period": "Annual",
    },
    {
        "title": "Statutory Dues Payment Challans (TDS, PF, ESI, Advance Tax)",
        "description": "Challans and quarterly returns for TDS (24Q, 26Q), PF/ESI monthly remittances, and advance tax payments.",
        "period": "Full Year",
    },
    {
        "title": "Related Party Transactions Register (Sec 188 / 184 / 189)",
        "description": "List of related parties, MBP-1 director declarations, and approvals for transactions entered during the fiscal year.",
        "period": "Annual",
    },
    {
        "title": "Board Meeting Minutes & Shareholder Resolutions",
        "description": "Certified copies of Board of Directors and AGM/EGM minutes approved during the financial year.",
        "period": "Annual",
    },
]
