"""Application DTOs for Report Generation, Approval, and Export."""

from dataclasses import dataclass

from finauditpro.domain.report_entities import ExportFormatEnum


@dataclass(frozen=True)
class GenerateReportDTO:
    engagement_id: str
    template_id: str
    title: str
    generated_by: str = "Lead Auditor"
    include_ai_findings: bool = True


@dataclass(frozen=True)
class ApproveReportDTO:
    report_id: str
    approved_by: str
    approver_role: str = "Audit Partner"
    note: str | None = None


@dataclass(frozen=True)
class ExportReportDTO:
    report_id: str
    export_format: ExportFormatEnum
    output_dir: str | None = None
