"""Pure domain entities and enumerations for Phase D Completion Checklist & Finalization Gate."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class ChecklistCategoryEnum(StrEnum):
    PLANNING = "Planning"
    RISK_ASSESSMENT = "Risk Assessment"
    AUDIT_PROCEDURES = "Audit Procedures"
    EVIDENCE = "Audit Evidence"
    SAMPLING = "Audit Sampling"
    EXCEPTIONS = "Audit Exceptions"
    MISSTATEMENTS = "Misstatement Evaluation (SA 450)"
    REVIEW_NOTES = "Review Notes Clearance"
    FINANCIAL_STATEMENTS = "Financial Statements (Schedule III)"
    NOTES_AND_DISCLOSURES = "Notes to Accounts & Disclosures"
    CASH_FLOW = "Cash Flow Statement (AS 3 / Ind AS 7)"
    CARO = "CARO 2020 Reporting"
    TAX_AUDIT = "Tax Audit / Form 3CD"
    RELATED_PARTIES = "Related Parties (SA 550)"
    GOING_CONCERN = "Going Concern Assessment (SA 570)"
    SUBSEQUENT_EVENTS = "Subsequent Events (SA 560)"
    MANAGEMENT_REPRESENTATION = "Written Representations (SA 580)"
    FINAL_ANALYTICAL_REVIEW = "Final Analytical Review (SA 520)"
    AUDIT_REPORT = "Audit Report Formulation"
    PARTNER_REVIEW = "Partner Sign-off & Final Review"


class CompletionStatusEnum(StrEnum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    NOT_APPLICABLE = "Not Applicable"
    BLOCKED = "Blocked"
    REQUIRES_REVIEW = "Requires Review"


class ItemSeverityEnum(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class CompletionChecklistItem(DomainBaseModel):
    """Traceable checklist item determining engagement finalization readiness."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    category: ChecklistCategoryEnum = Field(...)
    title: str = Field(...)
    description: str = Field(default="")
    is_applicable: bool = Field(default=True)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED)
    supporting_ref: str | None = Field(default=None)
    reviewer: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=utc_now)


class OpenItem(DomainBaseModel):
    """Unified cross-subsystem open item tracking issues blocking completion."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    source_type: str = Field(...)
    source_ref: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    severity: ItemSeverityEnum = Field(default=ItemSeverityEnum.MEDIUM)
    action_required: str = Field(...)
    is_blocking: bool = Field(default=True)
    resolved: bool = Field(default=False)


class FinalizationBlocker(DomainBaseModel):
    """Explainable blocking condition preventing audit completion and lock."""

    category: str = Field(...)
    reason: str = Field(...)
    source_ref: str = Field(...)
    action_required: str = Field(...)
    severity: ItemSeverityEnum = Field(default=ItemSeverityEnum.CRITICAL)


class FinalizationGateResult(DomainBaseModel):
    """Deterministic finalization gate assessment result."""

    is_finalizable: bool = Field(...)
    blockers: list[FinalizationBlocker] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    total_open_items: int = Field(default=0)
    critical_items_count: int = Field(default=0)


class RelatedPartyCompletionRecord(DomainBaseModel):
    """SA 550 Related Parties completion workpaper record."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    register_reviewed: bool = Field(default=True)
    undisclosed_transactions_identified: bool = Field(default=False)
    arms_length_verified: bool = Field(default=True)
    schedule_iii_disclosed: bool = Field(default=True)
    auditor_conclusion: str = Field(
        default="All material related party transactions identified, tested for arm's length, and disclosed in Note 28."
    )
    reviewer: str | None = Field(default=None)
    is_completed: bool = Field(default=True)


class SA240CompletionRecord(DomainBaseModel):
    """SA 240 Management Override & Irregularity Risk completion workpaper record."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    management_override_tested: bool = Field(default=True)
    journal_entry_testing_completed: bool = Field(default=True)
    revenue_recognition_presumption_addressed: bool = Field(default=True)
    risk_indicators_identified: bool = Field(default=False)
    auditor_conclusion: str = Field(
        default="Mandatory journal entry testing and management override procedures completed with zero unaddressed risk indicators."
    )
    reviewer: str | None = Field(default=None)
    is_completed: bool = Field(default=True)


FraudCompletionRecord = SA240CompletionRecord  # ignore
