"""
Audit Workflow State Models & Stage Enumerations for FinAuditPro.
Defines the strict 16-stage audit lifecycle sequence and state data representations.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

class AuditStage(str, Enum):
    """Ordered 16-Stage Enterprise Audit Lifecycle."""
    CLIENT_CREATED = "CLIENT_CREATED"
    FINANCIAL_YEAR_SELECTED = "FINANCIAL_YEAR_SELECTED"
    ENGAGEMENT_CREATED = "ENGAGEMENT_CREATED"
    MATERIALITY_DEFINED = "MATERIALITY_DEFINED"
    DOCUMENT_COLLECTION = "DOCUMENT_COLLECTION"
    OCR_PROCESSING = "OCR_PROCESSING"
    DOCUMENT_CLASSIFICATION = "DOCUMENT_CLASSIFICATION"
    AI_ANALYSIS = "AI_ANALYSIS"
    RISK_DETECTION = "RISK_DETECTION"
    WORKING_PAPERS_GENERATED = "WORKING_PAPERS_GENERATED"
    EVIDENCE_LINKED = "EVIDENCE_LINKED"
    REVIEW_NOTES = "REVIEW_NOTES"
    COMPLIANCE_REVIEW = "COMPLIANCE_REVIEW"
    PARTNER_REVIEW = "PARTNER_REVIEW"
    FINAL_REPORT = "FINAL_REPORT"
    AUDIT_COMPLETED = "AUDIT_COMPLETED"

    @classmethod
    def stage_order(cls) -> List["AuditStage"]:
        return [
            cls.CLIENT_CREATED,
            cls.FINANCIAL_YEAR_SELECTED,
            cls.ENGAGEMENT_CREATED,
            cls.MATERIALITY_DEFINED,
            cls.DOCUMENT_COLLECTION,
            cls.OCR_PROCESSING,
            cls.DOCUMENT_CLASSIFICATION,
            cls.AI_ANALYSIS,
            cls.RISK_DETECTION,
            cls.WORKING_PAPERS_GENERATED,
            cls.EVIDENCE_LINKED,
            cls.REVIEW_NOTES,
            cls.COMPLIANCE_REVIEW,
            cls.PARTNER_REVIEW,
            cls.FINAL_REPORT,
            cls.AUDIT_COMPLETED,
        ]

    def get_index(self) -> int:
        return AuditStage.stage_order().index(self)

    def is_after(self, other: "AuditStage") -> bool:
        return self.get_index() > other.get_index()

    def is_before(self, other: "AuditStage") -> bool:
        return self.get_index() < other.get_index()


class AuditStatus(str, Enum):
    """High-level Operational Status of an Audit Engagement."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REVIEW = "PENDING_REVIEW"
    PARTNER_APPROVED = "PARTNER_APPROVED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    ARCHIVED = "ARCHIVED"


@dataclass
class WorkflowState:
    """
    Represents the full runtime and persisted state of an Audit Engagement Workflow.
    """
    engagement_id: int
    client_id: int
    financial_year: str
    current_stage: AuditStage = AuditStage.CLIENT_CREATED
    audit_status: AuditStatus = AuditStatus.IN_PROGRESS
    completion_percentage: float = 0.0
    current_reviewer: Optional[str] = None
    pending_tasks: List[str] = field(default_factory=list)
    blocked_tasks: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    completion_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for JSON/storage persistence."""
        return {
            "engagement_id": self.engagement_id,
            "client_id": self.client_id,
            "financial_year": self.financial_year,
            "current_stage": self.current_stage.value,
            "audit_status": self.audit_status.value,
            "completion_percentage": round(self.completion_percentage, 2),
            "current_reviewer": self.current_reviewer,
            "pending_tasks": list(self.pending_tasks),
            "blocked_tasks": list(self.blocked_tasks),
            "last_updated": self.last_updated.isoformat(),
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Deserialize state from dict/storage."""
        return cls(
            engagement_id=data["engagement_id"],
            client_id=data["client_id"],
            financial_year=data["financial_year"],
            current_stage=AuditStage(data.get("current_stage", AuditStage.CLIENT_CREATED.value)),
            audit_status=AuditStatus(data.get("audit_status", AuditStatus.IN_PROGRESS.value)),
            completion_percentage=data.get("completion_percentage", 0.0),
            current_reviewer=data.get("current_reviewer"),
            pending_tasks=data.get("pending_tasks", []),
            blocked_tasks=data.get("blocked_tasks", []),
            last_updated=datetime.fromisoformat(data["last_updated"]) if isinstance(data.get("last_updated"), str) else datetime.utcnow(),
            completion_date=datetime.fromisoformat(data["completion_date"]) if data.get("completion_date") else None,
        )
