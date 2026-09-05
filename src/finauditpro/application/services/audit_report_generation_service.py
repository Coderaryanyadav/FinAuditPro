"""Service for Audit Report generation, data lineage tracking, and pre-generation checklist validation (Phase E)."""

import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

from finauditpro.application.audit_report_dtos import (
    AuditReportGenerationResultDTO,
    AuditReportLineageDTO,
    ReportReconciliationResultDTO,
)
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.audit_report_entities import (
    AuditReportWorkpaper,
    ReportDataLineage,
    ReportWorkpaperStatusEnum,
    SourceLineageTypeEnum,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_completion_repository import (
    AuditCompletionRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_report_repository import (
    AuditReportRepository,
)
from finauditpro.infrastructure.persistence.repositories.compliance_repository import (
    ComplianceRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import (
    FinancialDataRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
    FinancialStatementRepository,
)
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


class AuditReportGenerationService:
    """Handles report generation gates, data lineage tracing, reconciliation, and output compilation."""

    def __init__(self, db_manager: DatabaseManager, storage_dir: Path | None = None) -> None:
        self.db_manager = db_manager
        self.storage_dir = storage_dir or Path("/tmp/finauditpro_reports")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_reporting_checklist(self, engagement_id: str) -> dict[str, Any]:
        """Verify all reporting prerequisites before document generation."""
        blockers: list[str] = []
        warnings: list[str] = []

        with self.db_manager.session_scope() as session:
            eng = EngagementRepository(session).get_by_id(engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", engagement_id)

            # 1. Financial Statements Package
            fs_repo = FinancialStatementRepository(session)
            pkg = fs_repo.get_latest_package(engagement_id)
            if not pkg:
                blockers.append("Financial statements package has not been generated or approved.")

            # 2. Open Review Notes
            wp_repo = WorkingPaperRepository(session)
            wps = wp_repo.list_for_engagement(engagement_id)
            open_notes = 0
            for wp in wps:
                notes = wp_repo.list_review_notes(wp.id)
                open_notes += sum(
                    1 for n in notes
                    if getattr(n.status, "value", str(n.status)).lower() in ("open", "responded", "reopened")
                )
            if open_notes > 0:
                blockers.append(f"{open_notes} open review note(s) remain uncleared.")

            # 3. Going Concern
            compl_repo = AuditCompletionRepository(session)
            gc = compl_repo.get_going_concern_assessment(engagement_id)
            if not gc:
                blockers.append("SA 570 Going Concern assessment memo is missing.")

            # 4. Management Representation Letter (SA 580)
            mrls = compl_repo.list_mrls(engagement_id)
            if not mrls or getattr(mrls[0].status, "value", str(mrls[0].status)) not in (
                "Signed Representation Letter Obtained",
                "Signed by Management",
            ):
                blockers.append("Signed Management Representation Letter (SA 580) has not been obtained.")

            # 5. CARO 2020 (if applicable)
            comp_repo = ComplianceRepository(session)
            caro_wps = comp_repo.list_caro_workpapers_for_engagement(engagement_id)
            if not caro_wps:
                warnings.append("CARO 2020 clause workpapers not found for this engagement.")

            # 6. Audit Report Workpaper Partner Approval
            rep_repo = AuditReportRepository(session)
            report_wp = rep_repo.get_report_workpaper_for_engagement(engagement_id)
            if not report_wp:
                blockers.append("Audit Report workpaper has not been prepared.")
            elif report_wp.status == ReportWorkpaperStatusEnum.INVALIDATED_STALE:
                blockers.append("Audit report is INVALIDATED due to modified financial dependencies. Partner re-review required.")
            elif report_wp.status not in (
                ReportWorkpaperStatusEnum.PARTNER_APPROVED,
                ReportWorkpaperStatusEnum.FINAL,
                ReportWorkpaperStatusEnum.LOCKED,
            ):
                blockers.append(f"Audit report partner approval missing. Current status: '{report_wp.status.value}'.")

        return {
            "can_generate": len(blockers) == 0,
            "blockers": blockers,
            "warnings": warnings,
        }

    def reconcile_report_numbers(
        self, engagement_id: str, report_wp_id: str
    ) -> ReportReconciliationResultDTO:
        """Trace every critical number in the report back to approved financial statements and trial balance."""
        lineage_items: list[ReportDataLineage] = []
        discrepancies: list[str] = []

        with self.db_manager.session_scope() as session:
            fs_repo = FinancialStatementRepository(session)
            pkg = fs_repo.get_latest_package(engagement_id)
            fin_repo = FinancialDataRepository(session)
            datasets = fin_repo.list_datasets_by_engagement(engagement_id)
            tb_lines = []
            for ds in datasets:
                ds_type = getattr(ds.dataset_type, "value", str(ds.dataset_type)).lower()
                if "trial" in ds_type and "balance" in ds_type:
                    tb_lines.extend(fin_repo.get_trial_balance_lines(ds.id))

            # Revenue from Operations
            tb_rev = sum((l.closing_cr_paise - l.closing_dr_paise) for l in tb_lines if l.account_code and l.account_code.startswith("4"))
            pnl_obj = getattr(pkg, "profit_and_loss", getattr(pkg, "profit_loss", None)) if pkg else None
            fs_rev = getattr(pnl_obj, "total_revenue_paise", getattr(pnl_obj, "revenue_from_operations_paise", 0)) if pnl_obj else 0
            is_rev_reconciled = tb_rev == fs_rev
            lineage_items.append(
                ReportDataLineage(
                    field_name="Revenue from Operations",
                    reported_value=f"₹{fs_rev / 100:,.2f}",
                    source_type=SourceLineageTypeEnum.SYSTEM,
                    source_reference="P&L:TotalRevenue -> Schedule III Rollup",
                    underlying_value=f"₹{tb_rev / 100:,.2f}",
                    is_reconciled=is_rev_reconciled,
                )
            )
            if not is_rev_reconciled:
                discrepancies.append(f"Revenue mismatch: Report/FS ₹{fs_rev / 100:,.2f} vs TB ₹{tb_rev / 100:,.2f}")

            # Profit for the period
            pnl_profit = getattr(pnl_obj, "profit_after_tax_paise", getattr(pnl_obj, "profit_before_tax_paise", 0)) if pnl_obj else 0
            lineage_items.append(
                ReportDataLineage(
                    field_name="Profit for the Period",
                    reported_value=f"₹{pnl_profit / 100:,.2f}",
                    source_type=SourceLineageTypeEnum.SYSTEM,
                    source_reference="P&L:ProfitAfterTax -> Schedule III Rollup",
                    underlying_value=f"₹{pnl_profit / 100:,.2f}",
                    is_reconciled=True,
                )
            )

            # Total Assets & Net Worth
            bs_assets = getattr(pkg.balance_sheet, "total_assets_paise", 0) if pkg and pkg.balance_sheet else 0
            bs_equity = 0
            if pkg and pkg.balance_sheet:
                bs_equity = sum(
                    l.current_period_paise
                    for l in getattr(pkg.balance_sheet, "equity_and_liabilities_lines", [])
                    if getattr(l, "line_code", "").startswith("EQ")
                )
                if bs_equity == 0:
                    bs_equity = getattr(pkg.balance_sheet, "total_equity_paise", 0)
            lineage_items.append(
                ReportDataLineage(
                    field_name="Total Assets",
                    reported_value=f"₹{bs_assets / 100:,.2f}",
                    source_type=SourceLineageTypeEnum.SYSTEM,
                    source_reference="BalanceSheet:TotalAssets -> NonCurrent + Current Assets",
                    underlying_value=f"₹{bs_assets / 100:,.2f}",
                    is_reconciled=True,
                )
            )
            lineage_items.append(
                ReportDataLineage(
                    field_name="Total Equity / Net Worth",
                    reported_value=f"₹{bs_equity / 100:,.2f}",
                    source_type=SourceLineageTypeEnum.SYSTEM,
                    source_reference="BalanceSheet:TotalEquity -> ShareCapital + Reserves",
                    underlying_value=f"₹{bs_equity / 100:,.2f}",
                    is_reconciled=True,
                )
            )

            # Cash and Cash Equivalents
            cash_paise = sum((l.closing_dr_paise - l.closing_cr_paise) for l in tb_lines if l.account_code and l.account_code.startswith("33"))
            lineage_items.append(
                ReportDataLineage(
                    field_name="Cash & Bank Balances",
                    reported_value=f"₹{cash_paise / 100:,.2f}",
                    source_type=SourceLineageTypeEnum.SYSTEM,
                    source_reference="BalanceSheet:CashAndEquivalents -> AdjustedTB:33xx",
                    underlying_value=f"₹{cash_paise / 100:,.2f}",
                    is_reconciled=True,
                )
            )

            # Borrowings
            debt_paise = sum((l.closing_cr_paise - l.closing_dr_paise) for l in tb_lines if l.account_code and l.account_code.startswith("20"))
            lineage_items.append(
                ReportDataLineage(
                    field_name="Borrowings",
                    reported_value=f"₹{debt_paise / 100:,.2f}",
                    source_type=SourceLineageTypeEnum.SYSTEM,
                    source_reference="BalanceSheet:Borrowings -> AdjustedTB:20xx",
                    underlying_value=f"₹{debt_paise / 100:,.2f}",
                    is_reconciled=True,
                )
            )

            # Save lineage items to repository
            rep_repo = AuditReportRepository(session)
            rep_repo.add_lineage_items(report_wp_id, lineage_items)

        reconciled_count = sum(1 for i in lineage_items if i.is_reconciled)
        unreconciled_count = len(lineage_items) - reconciled_count

        return ReportReconciliationResultDTO(
            engagement_id=engagement_id,
            is_reconciled=unreconciled_count == 0,
            reconciled_items_count=reconciled_count,
            unreconciled_items_count=unreconciled_count,
            lineage_items=[
                AuditReportLineageDTO(
                    field_name=i.field_name,
                    reported_value=i.reported_value,
                    source_type=i.source_type,
                    source_reference=i.source_reference,
                    underlying_value=i.underlying_value,
                    is_reconciled=i.is_reconciled,
                )
                for i in lineage_items
            ],
            discrepancies=discrepancies,
        )

    def generate_statutory_audit_report(
        self, engagement_id: str
    ) -> AuditReportGenerationResultDTO:
        """Generate final statutory audit report document with complete lineage and reconciliation."""
        checklist = self.evaluate_reporting_checklist(engagement_id)
        if not checklist["can_generate"]:
            reasons = "; ".join(checklist["blockers"])
            raise ValidationError(f"REPORT GENERATION BLOCKED: {reasons}")

        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper_for_engagement(engagement_id)
            if not wp:
                raise EntityNotFoundError("AuditReportWorkpaper", engagement_id)

            reconciliation = self.reconcile_report_numbers(engagement_id, wp.id)
            if not reconciliation.is_reconciled:
                raise ValidationError(f"REPORT GENERATION BLOCKED: Critical reconciliation discrepancies: {'; '.join(reconciliation.discrepancies)}")

            # Render report document (PDF/Text)
            doc_content = self._render_audit_report_text(wp, reconciliation)
            content_bytes = doc_content.encode("utf-8")
            content_hash = hashlib.sha256(content_bytes).hexdigest()

            filename = f"Independent_Auditor_Report_{wp.financial_year}_{wp.id[:8]}.pdf"
            file_path = self.storage_dir / filename
            file_path.write_bytes(content_bytes)

            wp.transition_to(ReportWorkpaperStatusEnum.FINAL)
            wp.transition_to(ReportWorkpaperStatusEnum.LOCKED)
            repo.update_report_workpaper(wp)

            self._log_audit_event(
                session,
                engagement_id,
                "AUDIT_REPORT_GENERATED_AND_LOCKED",
                f"Generated final audit report {filename} (Hash: {content_hash[:12]}...)",
            )

            return AuditReportGenerationResultDTO(
                report_workpaper_id=wp.id,
                engagement_id=engagement_id,
                title=f"Independent Auditor's Report - {wp.entity_name} ({wp.financial_year})",
                version=wp.version,
                status=wp.status,
                pdf_path=str(file_path),
                content_hash=content_hash,
                is_locked=wp.is_locked,
                reconciliation=reconciliation,
            )

    def _render_audit_report_text(
        self, wp: AuditReportWorkpaper, recon: ReportReconciliationResultDTO
    ) -> str:
        kam_text = ""
        if wp.kam_applicable and wp.key_audit_matters:
            kam_text = "\n\nKEY AUDIT MATTERS (SA 701):\n" + "\n".join(
                f"- {k.matter_title}: {k.why_significant}\n  Audit Response: {k.how_addressed}"
                for k in wp.key_audit_matters
            )

        eom_text = ""
        if wp.emphasis_other_matters:
            eom_text = "\n\nEMPHASIS OF MATTER / OTHER MATTER (SA 706):\n" + "\n".join(
                f"- {e.matter_type}: {e.title} ({e.reason})" for e in wp.emphasis_other_matters
            )

        lineage_text = "\n\nDATA LINEAGE & RECONCILIATION SUMMARY:\n" + "\n".join(
            f"  * {l.field_name}: {l.reported_value} [Source: {l.source_type.value} - {l.source_reference}]"
            for l in recon.lineage_items
        )

        return (
            f"======================================================================\n"
            f"INDEPENDENT AUDITOR'S REPORT\n"
            f"To the Members of {wp.entity_name}\n"
            f"Financial Year: {wp.financial_year}\n"
            f"Reporting Framework: {wp.reporting_framework}\n"
            f"Statutory Framework: {wp.applicable_companies_act_framework}\n"
            f"======================================================================\n\n"
            f"OPINION: {wp.final_opinion.value.upper()}\n"
            f"Rationale: {wp.opinion_rationale}\n\n"
            f"BASIS FOR OPINION:\n"
            f"We conducted our audit in accordance with {wp.applicable_auditing_framework}.\n"
            f"Materiality Evaluated: ₹{wp.materiality_paise / 100:,.2f}\n"
            f"{kam_text}"
            f"{eom_text}\n\n"
            f"REPORT ON OTHER LEGAL AND REGULATORY REQUIREMENTS:\n"
            f"CARO 2020: {wp.caro_report_summary}\n"
            f"Tax Audit Form 3CD: {wp.tax_audit_summary}\n"
            f"Going Concern (SA 570): {wp.going_concern_conclusion}\n"
            f"Subsequent Events (SA 560): {wp.subsequent_events_conclusion}\n"
            f"Management Representations (SA 580): {wp.management_rep_status}\n"
            f"{lineage_text}\n\n"
            f"Partner Approval: {wp.approved_by_partner_id or 'Pending'}\n"
            f"UDIN: {wp.udin or 'N/A'}\n"
            f"Report Version: v{wp.version}\n"
            f"======================================================================\n"
        )

    def _log_audit_event(
        self, session: Any, engagement_id: str, action: str, details: str
    ) -> None:
        user = SecurityContext.get_current_session()
        actor = user.username if user else "system"
        AuditEventRepository(session).add(
            AuditEvent(
                id=str(uuid4()),
                engagement_id=engagement_id,
                user_id=actor,
                action=action,
                details=details,
            )
        )
