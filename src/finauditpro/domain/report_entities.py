"""Domain entities and state machine for Report Templates, Reports, and Artifacts."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import Field

from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import DomainBaseModel
from finauditpro.domain.exceptions import InvalidStateTransitionError


class ReportStatusEnum(StrEnum):
    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    SUPERSEDED = "Superseded"


class ReportTypeEnum(StrEnum):
    FINDINGS_SUMMARY = "findings_summary"
    MANAGEMENT_LETTER = "management_letter"
    EXCEPTIONS_SUMMARY = "exceptions_summary"
    ENGAGEMENT_SUMMARY = "engagement_summary"


class ExportFormatEnum(StrEnum):
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"


LEGAL_REPORT_TRANSITIONS: dict[ReportStatusEnum, set[ReportStatusEnum]] = {
    ReportStatusEnum.DRAFT: {ReportStatusEnum.UNDER_REVIEW, ReportStatusEnum.APPROVED},
    ReportStatusEnum.UNDER_REVIEW: {ReportStatusEnum.APPROVED, ReportStatusEnum.DRAFT},
    ReportStatusEnum.APPROVED: {ReportStatusEnum.SUPERSEDED},
    ReportStatusEnum.SUPERSEDED: set(),
}


class ReportTemplate(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1)
    report_type: ReportTypeEnum = Field(...)
    version: str = Field(default="1.0")
    section_structure_json: str = Field(default="[]")
    source: str = Field(default="Firm Policy Template (Editable)")
    jurisdiction: str | None = Field(default=None)
    effective_from: str = Field(default="2025-04-01")
    verified_statutory: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ReportArtifact(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    report_id: str = Field(...)
    format: ExportFormatEnum = Field(...)
    stored_document_id: str | None = Field(default=None)
    file_path: str = Field(..., min_length=1)
    content_hash: str = Field(..., min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)


class Report(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    template_id: str = Field(...)
    template_version: str = Field(default="1.0")
    title: str = Field(..., min_length=1)
    report_type: ReportTypeEnum = Field(...)
    status: ReportStatusEnum = Field(default=ReportStatusEnum.DRAFT)
    data_as_of: str = Field(...)
    content_model_json: str = Field(default="{}")
    content_hash: str = Field(..., min_length=64, max_length=64)
    generated_by: str = Field(..., min_length=1)
    reviewed_by: str | None = Field(default=None)
    approved_by: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def transition_to(self, new_status: ReportStatusEnum) -> None:
        allowed = LEGAL_REPORT_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError("Report", self.status.value, new_status.value)
        self.status = new_status
        self.updated_at = utc_now()


# Non-statutory default template definitions with verified_statutory: False
DEFAULT_REPORT_TEMPLATES = [
    ReportTemplate(
        id="tpl-findings-01",
        name="Audit Findings & Internal Control Exceptions Summary",
        report_type=ReportTypeEnum.FINDINGS_SUMMARY,
        version="1.0",
        section_structure_json='[{"id": "exec_summary", "title": "Executive Summary"}, {"id": "accepted_findings", "title": "Accepted Audit Findings"}, {"id": "exceptions_summary", "title": "Deterministic Exception Analysis"}]',
        source="FinAuditPro Standard Internal Findings Template",
        effective_from="2025-04-01",
        verified_statutory=False,
    ),
    ReportTemplate(
        id="tpl-mgmt-01",
        name="Management Letter & Audit Governance Communication",
        report_type=ReportTypeEnum.MANAGEMENT_LETTER,
        version="1.0",
        section_structure_json='[{"id": "governance_intro", "title": "Governance Introduction"}, {"id": "control_deficiencies", "title": "Internal Control Deficiencies"}, {"id": "management_recommendations", "title": "Auditor Recommendations"}]',
        source="FinAuditPro Management Communication Format",
        effective_from="2025-04-01",
        verified_statutory=False,
    ),
    ReportTemplate(
        id="tpl-eng-01",
        name="Full Engagement File & Working Paper Summary",
        report_type=ReportTypeEnum.ENGAGEMENT_SUMMARY,
        version="1.0",
        section_structure_json='[{"id": "engagement_scope", "title": "Engagement Scope & Materiality"}, {"id": "risk_matrix", "title": "Risk Assessment Register"}, {"id": "wp_index", "title": "Working Paper Index & Sign-Off Status"}]',
        source="FinAuditPro Master Engagement Summary",
        effective_from="2025-04-01",
        verified_statutory=False,
    ),
]
