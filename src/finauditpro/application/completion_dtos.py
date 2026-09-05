"""Application Data Transfer Objects for Phase D Completion Checklist & Finalization Gate."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateChecklistItemDTO:
    engagement_id: str
    item_id: str
    status: str
    is_applicable: bool | None = None
    supporting_ref: str | None = None
    reviewer: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ChecklistItemDTO:
    id: str
    engagement_id: str
    category: str
    title: str
    description: str
    is_applicable: bool
    status: str
    supporting_ref: str | None
    reviewer: str | None
    notes: str | None
    updated_at: str


@dataclass(frozen=True)
class OpenItemDTO:
    id: str
    engagement_id: str
    source_type: str
    source_ref: str
    title: str
    description: str
    severity: str
    action_required: str
    is_blocking: bool
    resolved: bool


@dataclass(frozen=True)
class OpenItemsRegisterDTO:
    engagement_id: str
    items: list[OpenItemDTO]
    total_open_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    informational_count: int


@dataclass(frozen=True)
class FinalizationBlockerDTO:
    category: str
    reason: str
    source_ref: str
    action_required: str
    severity: str


@dataclass(frozen=True)
class FinalizationGateResultDTO:
    engagement_id: str
    is_finalizable: bool
    blockers: list[FinalizationBlockerDTO]
    warnings: list[str]
    total_open_items: int
    critical_items_count: int

    @property
    def is_ready_for_finalization(self) -> bool:
        return self.is_finalizable


@dataclass(frozen=True)
class PartnerSignoffDTO:
    engagement_id: str
    signoff_notes: str
    audit_opinion_type: str = "Unmodified"
    udin: str | None = None


@dataclass(frozen=True)
class ArchiveManifestDTO:
    engagement_id: str
    client_name: str
    financial_year: str
    finalization_date: str
    finalized_by: str
    working_papers_count: int
    evidence_count: int
    financial_statements_count: int
    adjustments_count: int
    misstatements_count: int
    review_notes_count: int
    sealed_content_hash: str
    application_version: str = "FinAuditPro Enterprise 2026.1"
    retention_period_years: int = 8
    retention_until: str | None = None
    legal_hold: bool = False


@dataclass(frozen=True)
class RelatedPartyCompletionDTO:
    engagement_id: str
    register_reviewed: bool
    undisclosed_transactions_identified: bool
    arms_length_verified: bool
    schedule_iii_disclosed: bool
    auditor_conclusion: str
    reviewer: str | None = None


@dataclass(frozen=True)
class SA240CompletionDTO:
    engagement_id: str
    management_override_tested: bool
    journal_entry_testing_completed: bool
    revenue_recognition_presumption_addressed: bool
    risk_indicators_identified: bool
    auditor_conclusion: str
    reviewer: str | None = None


FraudCompletionDTO = SA240CompletionDTO  # ignore
