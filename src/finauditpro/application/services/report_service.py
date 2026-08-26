"""Service assembling real-query data, generating PDF/XLSX/CSV reports, and managing approval workflows."""

import hashlib
import json
from pathlib import Path
from typing import Any

import openpyxl

from finauditpro.application.report_dtos import ApproveReportDTO, ExportReportDTO, GenerateReportDTO
from finauditpro.application.services.report_renderer import render_pdf
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.domain.export_sanitizer import escape_formula_injection
from finauditpro.domain.report_entities import (
    ExportFormatEnum,
    Report,
    ReportArtifact,
    ReportStatusEnum,
    ReportTemplate,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.report_repository import ReportRepository
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


class ReportService:
    """Service handling report assembly, charts, PDF generation, formula-injection safe export, and approval."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def _artifact_directory(self, engagement_id: str, output_dir: str | None = None) -> Path:
        """Return an engagement-scoped, application-owned report directory."""
        if output_dir:
            directory = Path(output_dir)
        else:
            database_path = Path(str(self.db_manager.engine.url.database))
            directory = database_path.parent / "reports" / engagement_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def list_reports(self, engagement_id: str) -> list[Report]:
        """List all reports for an engagement."""
        with self.db_manager.session_scope() as session:
            report_repo = ReportRepository(session)
            return report_repo.list_for_engagement(engagement_id)

    def list_templates(self) -> list[ReportTemplate]:
        """List all available report templates."""
        with self.db_manager.session_scope() as session:
            report_repo = ReportRepository(session)
            return report_repo.list_templates()

    def assemble_report_data(self, engagement_id: str) -> dict[str, Any]:
        """Assemble content strictly from real queries against the database."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            wp_repo = WorkingPaperRepository(session)
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(engagement_id)
            client_name, client_pan, client_cin, fy = "Client Entity", "", "", "2025-26"
            if eng:
                fy = str(eng.financial_year)
                from finauditpro.infrastructure.persistence.repositories import ClientRepository
                cli = ClientRepository(session).get_by_id(eng.client_id)
                if cli:
                    client_name = cli.name
                    client_pan = getattr(cli, "pan", "") or ""
                    client_cin = getattr(cli, "cin", "") or ""

            # 1. Findings
            findings = matrix_repo.list_findings_for_engagement(engagement_id)
            findings_data = [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity.value
                    if hasattr(f.severity, "value")
                    else str(f.severity),
                    "status": f.status.value if hasattr(f.status, "value") else str(f.status),
                    "source": f.source.value if hasattr(f.source, "value") else str(f.source),
                    "is_ai_generated": getattr(f, "is_ai_generated", False),
                    "amount_paise": f.amount_paise,
                    "description": f.description,
                }
                for f in findings
            ]

            # 2. Risks & Materiality
            risks = matrix_repo.list_risks_for_engagement(engagement_id)
            risks_data = [
                {
                    "code": r.risk_code,
                    "title": r.title,
                    "category": r.category,
                    "romm": r.derived_romm.value
                    if hasattr(r.derived_romm, "value")
                    else str(r.derived_romm),
                }
                for r in risks
            ]

            materiality = matrix_repo.get_latest_materiality(engagement_id)
            mat_data = (
                {
                    "overall_materiality_paise": materiality.overall_materiality_paise,
                    "performance_materiality_paise": materiality.performance_materiality_paise,
                    "summary_of_unadjusted_misstatements_paise": materiality.clearly_trivial_threshold_paise,
                    "benchmark": materiality.benchmark_type.value
                    if hasattr(materiality.benchmark_type, "value")
                    else str(materiality.benchmark_type),
                }
                if materiality
                else None
            )

            # 3. Working Papers
            wps = wp_repo.list_for_engagement(engagement_id)
            wp_data = [
                {
                    "ref": wp.index_reference,
                    "title": wp.title,
                    "area": wp.area,
                    "status": wp.status.value,
                    "preparer": wp.preparer_id,
                    "is_locked": wp.is_locked,
                }
                for wp in wps
            ]

            return {
                "engagement_id": engagement_id,
                "client_name": client_name,
                "client_pan": client_pan,
                "client_cin": client_cin,
                "financial_year": fy,
                "as_of": utc_now().isoformat(),
                "findings": findings_data,
                "risks": risks_data,
                "materiality": mat_data,
                "working_papers": wp_data,
            }


    def generate_report(self, dto: GenerateReportDTO) -> Report:
        """Assemble report data, compute content hash digest, and render PDF artifact."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            report_repo = ReportRepository(session)
            tpl = report_repo.get_template(dto.template_id)
            if not tpl:
                raise EntityNotFoundError("ReportTemplate", dto.template_id)

            assembled_data = self.assemble_report_data(dto.engagement_id)
            content_json = json.dumps(assembled_data, sort_keys=True)
            content_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()

            report = Report(
                engagement_id=dto.engagement_id,
                template_id=tpl.id,
                template_version=tpl.version,
                title=dto.title,
                report_type=tpl.report_type,
                status=ReportStatusEnum.DRAFT,
                data_as_of=assembled_data["as_of"],
                content_model_json=content_json,
                content_hash=content_hash,
                generated_by=dto.generated_by,
            )
            saved_report = report_repo.add_report(report)

            # Build PDF output
            output_dir = self._artifact_directory(dto.engagement_id)
            pdf_path = output_dir / f"report_{saved_report.id}.pdf"
            render_pdf(saved_report, assembled_data, pdf_path, is_draft=True)

            # Record Artifact
            pdf_bytes = pdf_path.read_bytes()
            art_hash = hashlib.sha256(pdf_bytes).hexdigest()
            artifact = ReportArtifact(
                report_id=saved_report.id,
                format=ExportFormatEnum.PDF,
                file_path=str(pdf_path),
                content_hash=art_hash,
            )
            report_repo.add_artifact(artifact)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.generated_by,
                    action="Report Generated",
                    details=f"Generated report '{saved_report.title}' (v{saved_report.template_version}). Content Hash: {content_hash[:16]}...",
                )
            )

            return saved_report

    def export_to_xlsx(self, dto: ExportReportDTO) -> str:
        """Export findings and engagement data to XLSX with mandatory formula-injection escaping."""
        with self.db_manager.session_scope() as session:
            report_repo = ReportRepository(session)
            report = report_repo.get_report(dto.report_id)
            if not report:
                raise EntityNotFoundError("Report", dto.report_id)

            data = json.loads(report.content_model_json)
            wb = openpyxl.Workbook()

            # Sheet 1: Findings
            ws_findings = wb.active
            ws_findings.title = "Accepted Findings"
            ws_findings.append(
                ["Finding ID", "Title", "Severity", "Status", "Amount (Paise)", "Description"]
            )

            for f in data.get("findings", []):
                row = [
                    escape_formula_injection(f.get("id")),
                    escape_formula_injection(f.get("title")),
                    escape_formula_injection(f.get("severity")),
                    escape_formula_injection(f.get("status")),
                    escape_formula_injection(f.get("amount_paise")),
                    escape_formula_injection(f.get("description")),
                ]
                ws_findings.append(row)

            # Sheet 2: Working Papers
            ws_wp = wb.create_sheet(title="Working Papers")
            ws_wp.append(["Ref Code", "Title", "Area", "Status", "Preparer", "Locked"])

            for wp in data.get("working_papers", []):
                row = [
                    escape_formula_injection(wp.get("ref")),
                    escape_formula_injection(wp.get("title")),
                    escape_formula_injection(wp.get("area")),
                    escape_formula_injection(wp.get("status")),
                    escape_formula_injection(wp.get("preparer")),
                    escape_formula_injection(str(wp.get("is_locked"))),
                ]
                ws_wp.append(row)

            out_dir = self._artifact_directory(report.engagement_id, dto.output_dir)
            out_path = out_dir / f"report_{report.id}.xlsx"
            wb.save(str(out_path))

            xlsx_bytes = out_path.read_bytes()
            art_hash = hashlib.sha256(xlsx_bytes).hexdigest()
            artifact = ReportArtifact(
                report_id=report.id,
                format=ExportFormatEnum.XLSX,
                file_path=str(out_path),
                content_hash=art_hash,
            )
            report_repo.add_artifact(artifact)
            return str(out_path)

    def export_to_csv(self, dto: ExportReportDTO) -> str:
        """Export findings to CSV with mandatory formula-injection escaping."""
        import csv

        with self.db_manager.session_scope() as session:
            report_repo = ReportRepository(session)
            report = report_repo.get_report(dto.report_id)
            if not report:
                raise EntityNotFoundError("Report", dto.report_id)

            data = json.loads(report.content_model_json)
            out_dir = self._artifact_directory(report.engagement_id, dto.output_dir)
            out_path = out_dir / f"report_{report.id}.csv"

            with out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Finding ID", "Title", "Severity", "Status", "Amount (Paise)", "Description"]
                )

                for find in data.get("findings", []):
                    writer.writerow(
                        [
                            escape_formula_injection(find.get("id")),
                            escape_formula_injection(find.get("title")),
                            escape_formula_injection(find.get("severity")),
                            escape_formula_injection(find.get("status")),
                            escape_formula_injection(find.get("amount_paise")),
                            escape_formula_injection(find.get("description")),
                        ]
                    )

            csv_bytes = out_path.read_bytes()
            art_hash = hashlib.sha256(csv_bytes).hexdigest()
            artifact = ReportArtifact(
                report_id=report.id,
                format=ExportFormatEnum.CSV,
                file_path=str(out_path),
                content_hash=art_hash,
            )
            report_repo.add_artifact(artifact)
            return str(out_path)

    def approve_report(self, dto: ApproveReportDTO) -> Report:
        """Approve report, removing draft watermark and recording legal disclaimer."""
        with self.db_manager.session_scope() as session:
            from finauditpro.application.security.rbac import RBACManager, UserSession
            from finauditpro.domain.entities import RoleEnum
            role = RoleEnum.PARTNER if "partner" in dto.approver_role.lower() else (RoleEnum.MANAGER if "manager" in dto.approver_role.lower() else RoleEnum.ASSOCIATE)
            RBACManager(UserSession(user_id=dto.approved_by, username=dto.approved_by, role=role)).require_permission("engagement:signoff")

            report_repo = ReportRepository(session)
            report = report_repo.get_report(dto.report_id)
            if not report:
                raise EntityNotFoundError("Report", dto.report_id)


            report.transition_to(ReportStatusEnum.APPROVED)
            report.approved_by = dto.approved_by
            updated = report_repo.update_report(report)

            # Re-render PDF without DRAFT watermark
            data = json.loads(report.content_model_json)
            out_dir = self._artifact_directory(report.engagement_id)
            pdf_path = str(out_dir / f"report_{report.id}.pdf")
            render_pdf(updated, data, Path(pdf_path), is_draft=False)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=report.engagement_id,
                    actor=dto.approved_by,
                    action="Report Approved",
                    details=f"Approved report '{report.title}' by {dto.approver_role} {dto.approved_by}",
                )
            )
            return updated
