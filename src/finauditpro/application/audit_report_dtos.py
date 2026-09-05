"""Application Data Transfer Objects (DTOs) for Audit Reporting & Deliverables (Phase E)."""

from pydantic import Field

from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    CandidateKAMSourceEnum,
    ReportWorkpaperStatusEnum,
    SourceLineageTypeEnum,
)
from finauditpro.domain.entities import DomainBaseModel


class CreateAuditReportWorkpaperDTO(DomainBaseModel):
    engagement_id: str
    reporting_framework: str = "Companies Act 2013 / Ind AS"
    applicable_companies_act_framework: str = "Section 143(3) of Companies Act, 2013"
    applicable_auditing_framework: str = "Standards on Auditing (ICAI)"
    proposed_opinion: AuditOpinionTypeEnum = AuditOpinionTypeEnum.UNMODIFIED
    final_opinion: AuditOpinionTypeEnum = AuditOpinionTypeEnum.UNMODIFIED
    opinion_rationale: str = "Unmodified opinion based on sufficient appropriate audit evidence obtained."
    kam_applicable: bool = True
    caro_applicable: bool = True
    tax_audit_applicable: bool = True


class UpdateAuditReportWorkpaperDTO(DomainBaseModel):
    reporting_framework: str | None = None
    proposed_opinion: AuditOpinionTypeEnum | None = None
    final_opinion: AuditOpinionTypeEnum | None = None
    opinion_rationale: str | None = None
    kam_applicable: bool | None = None
    caro_applicable: bool | None = None
    tax_audit_applicable: bool | None = None
    udin: str | None = None


class AddBasisOfOpinionItemDTO(DomainBaseModel):
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


class AddKeyAuditMatterDTO(DomainBaseModel):
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


class AddEmphasisOrOtherMatterDTO(DomainBaseModel):
    matter_type: str = "Emphasis of Matter"
    title: str
    reason: str
    fs_reference: str
    audit_evidence_ref: str
    partner_decision: str
    final_wording: str


class PartnerApproveReportDTO(DomainBaseModel):
    engagement_id: str
    report_workpaper_id: str
    approval_notes: str
    udin: str | None = None


class CheckReportConsistencyDTO(DomainBaseModel):
    engagement_id: str


class AuditReportLineageDTO(DomainBaseModel):
    field_name: str
    reported_value: str
    source_type: SourceLineageTypeEnum
    source_reference: str
    underlying_value: str
    is_reconciled: bool = True


class ReportReconciliationResultDTO(DomainBaseModel):
    engagement_id: str
    is_reconciled: bool
    reconciled_items_count: int
    unreconciled_items_count: int
    lineage_items: list[AuditReportLineageDTO] = Field(default_factory=list)
    discrepancies: list[str] = Field(default_factory=list)


class AuditReportGenerationResultDTO(DomainBaseModel):
    report_workpaper_id: str
    engagement_id: str
    title: str
    version: int
    status: ReportWorkpaperStatusEnum
    pdf_path: str
    content_hash: str
    is_locked: bool
    reconciliation: ReportReconciliationResultDTO | None = None
