"""Domain entities and value objects for Professional Audit Reporting (Phase E).

Encapsulates SA 700 / SA 705 / SA 706 / SA 701 compliance, structured opinion
decision support, Key Audit Matters (KAM), Basis for Opinion, and Data Lineage.
"""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4
from pydantic import Field

from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import DomainBaseModel
from finauditpro.domain.exceptions import InvalidStateTransitionError


class AuditOpinionTypeEnum(StrEnum):
    UNMODIFIED = "Unmodified Opinion"
    QUALIFIED = "Qualified Opinion"
    ADVERSE = "Adverse Opinion"
    DISCLAIMER = "Disclaimer of Opinion"


class OpinionFactorEnum(StrEnum):
    MATERIAL_MISSTATEMENT = "Material Misstatement in Financial Statements"
    SCOPE_LIMITATION = "Scope Limitation / Inability to Obtain SAAE"
    MATERIAL_NOT_PERVASIVE = "Material but Not Pervasive"
    MATERIAL_AND_PERVASIVE = "Material and Pervasive"
    GOING_CONCERN_UNCERTAINTY = "Material Uncertainty Related to Going Concern"


class ReportWorkpaperStatusEnum(StrEnum):
    DRAFT = "Draft"
    REVIEWED_DRAFT = "Reviewed Draft"
    PARTNER_APPROVED = "Partner Approved"
    FINAL = "Final"
    LOCKED = "Locked"
    INVALIDATED_STALE = "Invalidated / Review Required"
    SUPERSEDED = "Superseded"


class SourceLineageTypeEnum(StrEnum):
    SYSTEM = "System Derived"
    MANUAL = "Manual"
    SYSTEM_OVERRIDE = "System + Manual Override"


class CandidateKAMSourceEnum(StrEnum):
    SIGNIFICANT_RISK = "Significant Audit Risk Identified"
    AUDITOR_JUDGMENT = "Area of Significant Auditor Judgment"
    MANAGEMENT_ESTIMATE = "High Degree of Estimation Uncertainty"
    MAJOR_ADJUSTMENT = "Material Audit Adjustment Recorded"
    COMPLEX_TRANSACTION = "Complex / Non-Routine Transaction"


LEGAL_REPORT_WP_TRANSITIONS: dict[ReportWorkpaperStatusEnum, set[ReportWorkpaperStatusEnum]] = {
    ReportWorkpaperStatusEnum.DRAFT: {
        ReportWorkpaperStatusEnum.REVIEWED_DRAFT,
        ReportWorkpaperStatusEnum.PARTNER_APPROVED,
    },
    ReportWorkpaperStatusEnum.REVIEWED_DRAFT: {
        ReportWorkpaperStatusEnum.PARTNER_APPROVED,
        ReportWorkpaperStatusEnum.DRAFT,
    },
    ReportWorkpaperStatusEnum.PARTNER_APPROVED: {
        ReportWorkpaperStatusEnum.FINAL,
        ReportWorkpaperStatusEnum.LOCKED,
        ReportWorkpaperStatusEnum.INVALIDATED_STALE,
        ReportWorkpaperStatusEnum.DRAFT,
    },
    ReportWorkpaperStatusEnum.FINAL: {
        ReportWorkpaperStatusEnum.LOCKED,
        ReportWorkpaperStatusEnum.INVALIDATED_STALE,
        ReportWorkpaperStatusEnum.SUPERSEDED,
    },
    ReportWorkpaperStatusEnum.LOCKED: {
        ReportWorkpaperStatusEnum.INVALIDATED_STALE,
        ReportWorkpaperStatusEnum.SUPERSEDED,
    },
    ReportWorkpaperStatusEnum.INVALIDATED_STALE: {
        ReportWorkpaperStatusEnum.DRAFT,
        ReportWorkpaperStatusEnum.PARTNER_APPROVED,
        ReportWorkpaperStatusEnum.SUPERSEDED,
    },
    ReportWorkpaperStatusEnum.SUPERSEDED: set(),
}


class BasisOfOpinionItem(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    issue_title: str
    financial_area: str
    assertion: str
    procedure_ref: str
    evidence_ref: str
    finding_description: str
    misstatement_paise: int = 0
    is_material: bool = False
    is_pervasive: bool = False
    management_response: str = ""
    auditor_conclusion: str = ""
    partner_decision: str = ""


class KeyAuditMatter(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    matter_title: str
    why_significant: str
    how_addressed: str
    fs_reference: str
    wp_references: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    partner_conclusion: str = ""
    final_disclosure_text: str = ""
    is_candidate: bool = False
    candidate_source: CandidateKAMSourceEnum | None = None


class EmphasisOrOtherMatter(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    matter_type: str = "Emphasis of Matter"  # or "Other Matter"
    title: str
    reason: str
    fs_reference: str
    audit_evidence_ref: str
    partner_decision: str
    final_wording: str


class ReportDataLineage(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    field_name: str
    reported_value: str
    source_type: SourceLineageTypeEnum
    source_reference: str
    underlying_value: str
    is_reconciled: bool = True


class ConsistencyIssue(DomainBaseModel):
    category: str
    field_name: str
    source_a: str
    value_a: str
    source_b: str
    value_b: str
    severity: str  # "Critical", "Warning"
    explanation: str


class AuditReportWorkpaper(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    reporting_framework: str = "Companies Act 2013 / Ind AS"
    financial_year: str
    entity_name: str
    applicable_companies_act_framework: str = "Section 143(3) of Companies Act, 2013"
    applicable_auditing_framework: str = "Standards on Auditing (ICAI)"
    materiality_paise: int = 0
    proposed_opinion: AuditOpinionTypeEnum = AuditOpinionTypeEnum.UNMODIFIED
    final_opinion: AuditOpinionTypeEnum = AuditOpinionTypeEnum.UNMODIFIED
    opinion_rationale: str = "Unmodified opinion based on sufficient appropriate audit evidence obtained."
    basis_of_opinion_items: list[BasisOfOpinionItem] = Field(default_factory=list)
    kam_applicable: bool = True
    key_audit_matters: list[KeyAuditMatter] = Field(default_factory=list)
    emphasis_other_matters: list[EmphasisOrOtherMatter] = Field(default_factory=list)
    caro_applicable: bool = True
    caro_report_summary: str = "CARO 2020 annexure included."
    tax_audit_applicable: bool = True
    tax_audit_summary: str = "Form 3CD tax audit report annexure."
    going_concern_conclusion: str = "No material uncertainty identified"
    subsequent_events_conclusion: str = "No adjusting subsequent events identified"
    misstatements_summary: str = "All material misstatements corrected"
    management_rep_status: str = "Signed Representation Letter Obtained"
    status: ReportWorkpaperStatusEnum = ReportWorkpaperStatusEnum.DRAFT
    version: int = 1
    is_locked: bool = False
    preparer_id: str = "auditor"
    reviewer_id: str | None = None
    approved_by_partner_id: str | None = None
    approved_at: datetime | None = None
    dependency_hash: str = ""
    udin: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def transition_to(self, new_status: ReportWorkpaperStatusEnum) -> None:
        allowed = LEGAL_REPORT_WP_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                "AuditReportWorkpaper", self.status.value, new_status.value
            )
        self.status = new_status
        self.updated_at = utc_now()
        if new_status == ReportWorkpaperStatusEnum.LOCKED:
            self.is_locked = True
        elif new_status in (ReportWorkpaperStatusEnum.INVALIDATED_STALE, ReportWorkpaperStatusEnum.DRAFT):
            self.is_locked = False
