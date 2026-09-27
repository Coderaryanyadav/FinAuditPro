"""Application service orchestrating financial dataset import, validation preview, reconciliations, analytics, and audit work creation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.financial_dtos import (
    CreateAuditWorkDTO,
    ImportDatasetDTO as AppImportDTO,
    RunReconciliationDTO,
    ValidationPreviewDTO,
)
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.audit_execution_entities import AuditException, TestExecution
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.domain.bank_reconciliation_engine import BankReconciliationEngine, BRSExceptionSeverityEnum
from finauditpro.domain.continuous_reconciliation_engine import ContinuousReconciliationEngine
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.domain.financial_entities import (
    DatasetStatusEnum,
    DatasetTypeEnum,
    ExceptionItem,
    ExceptionStatusEnum,
    FinancialDataset,
    Finding,
)
from finauditpro.domain.fixed_asset_engine import AssetAnomalyTypeEnum, FixedAssetEngine
from finauditpro.domain.gst_reconciliation_engine import GSTReconciliationEngine, MatchStatusEnum
from finauditpro.domain.value_objects import Money
from finauditpro.infrastructure.analytics.analytics_engine import DeterministicAnalyticsEngine
from finauditpro.infrastructure.analytics.column_detector import detect_column_mappings
from finauditpro.infrastructure.documents.document_security import calculate_sha256, sanitize_filename
from finauditpro.infrastructure.financial.financial_importer import FinancialImporter
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import AuditEventRepository
from finauditpro.infrastructure.persistence.repositories.engagement_repository import EngagementRepository
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import FinancialDataRepository


@dataclass(frozen=True)
class ImportDatasetDTO:
    engagement_id: str
    file_path: str
    dataset_type: DatasetTypeEnum = DatasetTypeEnum.GENERAL_LEDGER
    custom_mappings: dict[str, str] = field(default_factory=dict)


class FinancialService:
    """Service managing dataset ingestion, validation preview, reconciliations, analytics, and audit work generation."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def inspect_dataset_headers(self, file_path: str) -> tuple[list[str], dict[str, str]]:
        path = Path(file_path)
        if not path.is_file():
            raise EntityNotFoundError("Dataset File", file_path)
        headers, _rows = FinancialImporter.read_tabular_rows(path)
        return headers, detect_column_mappings(headers)

    def preview_dataset_import(
        self,
        file_path: str,
        dataset_type: DatasetTypeEnum = DatasetTypeEnum.GENERAL_LEDGER,
        custom_mappings: dict[str, str] | None = None,
    ) -> ValidationPreviewDTO:
        path = Path(file_path)
        if not path.is_file():
            raise EntityNotFoundError("Dataset File", file_path)
        headers, rows = FinancialImporter.read_tabular_rows(path)
        final_mappings = {**detect_column_mappings(headers), **(custom_mappings or {})}
        return FinancialImporter.validate_and_preview(dataset_type, rows, final_mappings, str(path))

    def import_dataset(self, dto: ImportDatasetDTO | AppImportDTO) -> FinancialDataset:
        path = Path(dto.file_path)
        if not path.is_file():
            raise EntityNotFoundError("Dataset File", dto.file_path)
        c_hash = calculate_sha256(path)
        headers, rows = FinancialImporter.read_tabular_rows(path)
        mappings = getattr(dto, "column_mappings", None) or getattr(dto, "custom_mappings", {})
        final_mappings = {**detect_column_mappings(headers), **mappings}
        dataset_id = str(uuid4())

        if dto.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
            imp_res = FinancialImporter.import_trial_balance(dataset_id, rows, final_mappings)
        elif dto.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
            imp_res = FinancialImporter.import_bank_statement(dataset_id, rows, final_mappings)
        else:
            imp_res = FinancialImporter.import_general_ledger(dataset_id, rows, final_mappings)

        dataset = FinancialDataset(
            id=dataset_id, engagement_id=dto.engagement_id, dataset_name=sanitize_filename(path.name),
            dataset_type=dto.dataset_type, filename=sanitize_filename(path.name), content_hash=c_hash,
            stored_path=str(path.resolve()), status=DatasetStatusEnum.IMPORTED if imp_res.valid_rows else DatasetStatusEnum.FAILED,
            total_rows=imp_res.total_rows, row_count=len(imp_res.valid_rows), error_rows=len(imp_res.errors),
            column_mappings=final_mappings, errors=imp_res.errors,
        )

        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)
            repo = FinancialDataRepository(session)
            saved_ds = repo.add_dataset(dataset)
            if dto.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
                repo.add_trial_balance_lines(imp_res.valid_rows)
            elif dto.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
                repo.add_bank_transactions(imp_res.valid_rows)
            else:
                repo.add_ledger_entries(imp_res.valid_rows)
            AuditEventRepository(session).add(AuditEvent(
                engagement_id=dto.engagement_id, actor="Auditor", action="Financial Dataset Imported",
                details=f"Imported '{dataset.dataset_name}' ({len(imp_res.valid_rows)} valid, {len(imp_res.errors)} errors).",
            ))
        return saved_ds

    def list_datasets_for_engagement(self, engagement_id: str) -> list[FinancialDataset]:
        with self.db_manager.session_scope() as session:
            return FinancialDataRepository(session).list_datasets_by_engagement(engagement_id)

    def list_dataset_rows(self, dataset_id: str) -> list[dict[str, Any]]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            ds = repo.get_dataset_by_id(dataset_id)
            if not ds:
                return []
            if ds.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
                return [{"row_no": l.source_row_no, "date": "-", "voucher_no": l.account_code or "-",
                         "account_name": l.account_name, "debit": Money(paise=l.debit_paise).formatted,
                         "credit": Money(paise=l.credit_paise).formatted, "narration": f"Closing Dr: {Money(paise=l.closing_dr_paise).formatted}"}
                        for l in repo.get_trial_balance_lines(dataset_id)]
            if ds.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
                return [{"row_no": t.source_row_no, "date": t.txn_date or "-", "voucher_no": t.txn_id or "-",
                         "account_name": t.description, "debit": Money(paise=t.debit_paise).formatted,
                         "credit": Money(paise=t.credit_paise).formatted, "narration": f"Balance: {Money(paise=t.balance_paise).formatted}"}
                        for t in repo.get_bank_transactions(dataset_id)]
            return [{"row_no": e.source_row_no, "date": e.entry_date or "-", "voucher_no": e.voucher_number or "-",
                     "account_name": e.account_name or "-", "debit": Money(paise=e.debit_paise).formatted,
                     "credit": Money(paise=e.credit_paise).formatted, "narration": e.narration or "-"}
                    for e in repo.get_ledger_entries(dataset_id)]

    def run_deterministic_analytics(self, dataset_id: str) -> list[ExceptionItem]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            ds = repo.get_dataset_by_id(dataset_id)
            if not ds:
                raise EntityNotFoundError("Financial Dataset", dataset_id)
            exceptions, run_id = [], str(uuid4())
            if ds.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
                exceptions.extend(DeterministicAnalyticsEngine.check_trial_balance_balances(dataset_id, repo.get_trial_balance_lines(dataset_id)).exceptions)
            elif ds.dataset_type in (DatasetTypeEnum.GENERAL_LEDGER, DatasetTypeEnum.JOURNAL_ENTRIES):
                entries = repo.get_ledger_entries(dataset_id)
                for fn in (DeterministicAnalyticsEngine.detect_duplicates, DeterministicAnalyticsEngine.detect_large_amount_outliers,
                           DeterministicAnalyticsEngine.detect_round_number_amounts, DeterministicAnalyticsEngine.detect_weekend_postings,
                           DeterministicAnalyticsEngine.detect_sequence_gaps, DeterministicAnalyticsEngine.check_benford_law):
                    exceptions.extend(fn(dataset_id, entries).exceptions)
            elif ds.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
                exceptions.extend(DeterministicAnalyticsEngine.check_bank_balance_continuity(dataset_id, repo.get_bank_transactions(dataset_id)).exceptions)

            for exc in exceptions:
                exc.analysis_run_id = run_id
            if exceptions:
                repo.add_exceptions(exceptions)
            AuditEventRepository(session).add(AuditEvent(
                engagement_id=ds.engagement_id, actor="System Analytics", action="Deterministic Analytics Completed",
                details=f"Analyzed '{ds.dataset_name}'. Flagged {len(exceptions)} exceptions.",
            ))
        return exceptions

    def run_reconciliation(self, dto: RunReconciliationDTO) -> list[ExceptionItem]:
        excs, r_id, r_type = [], str(uuid4()), dto.reconciliation_type.upper()

        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            target_ds = repo.get_dataset_by_id(dto.dataset_id) if dto.dataset_id else None
            if not target_ds:
                target_ds = repo.add_dataset(
                    FinancialDataset(
                        id=str(uuid4()),
                        engagement_id=dto.engagement_id,
                        dataset_name=f"Reconciliation Dataset ({r_type})",
                        dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
                        status=DatasetStatusEnum.IMPORTED,
                    )
                )
            ds_id = target_ds.id


            if r_type == "TB_BALANCE":
                res = ContinuousReconciliationEngine().reconcile_trial_balance(dto.data.get("tb_lines", []))
                if res.status != "BALANCED":
                    excs.append(ExceptionItem(
                        analysis_run_id=r_id, dataset_id=ds_id, analytic_id="TB_BALANCE_RECONCILIATION",
                        severity="High", title="Trial Balance Discrepancy", description=res.details,
                        computed_evidence=f"Discrepancy: ₹{res.difference_paise / 100:,.2f}",
                    ))
            elif r_type == "SUBLEDGER_GL":
                gl_b, s_t = int(dto.data.get("gl_account_balance_paise", 0)), int(dto.data.get("subledger_total_paise", 0))
                s_name = dto.data.get("subledger_name", "Subledger")
                res = ContinuousReconciliationEngine().reconcile_subledger_to_gl(s_name, gl_b, s_t)
                if res.status != "BALANCED":
                    excs.append(ExceptionItem(
                        analysis_run_id=r_id, dataset_id=ds_id, analytic_id="SUBLEDGER_GL_RECONCILIATION",
                        severity="High", title=f"{s_name} Control Account Discrepancy", description=res.details,
                        computed_evidence=f"GL: ₹{gl_b / 100:,.2f} | Subledger: ₹{s_t / 100:,.2f} | Diff: ₹{res.difference_paise / 100:,.2f}",
                    ))
            elif r_type == "BRS":
                sum_brs = BankReconciliationEngine.audit_brs_statement(dto.engagement_id, dto.as_of_date, dto.data.get("items", []))
                for r in sum_brs.records:
                    if r.exception_severity != BRSExceptionSeverityEnum.NORMAL_TIMING_DIFFERENCE:
                        excs.append(ExceptionItem(
                            analysis_run_id=r_id, dataset_id=ds_id, analytic_id="BRS_RECONCILIATION_EXCEPTION",
                            severity="High" if r.exception_severity == BRSExceptionSeverityEnum.DELAYED_BANKING_RISK else "Medium",
                            title=f"BRS Exception: {r.exception_severity.value}",
                            description=f"Account: {r.bank_account_number}, Ref: {r.reference_number}, {r.audit_recommendation}",
                            computed_evidence=f"Days: {r.days_outstanding}, Amount: ₹{r.amount_paise / 100:,.2f}",
                        ))
            elif r_type == "GST_2B":
                sum_gst = GSTReconciliationEngine.match_purchase_register_with_2b(dto.engagement_id, dto.data.get("books_invoices", []), dto.data.get("gstr2b_invoices", []))
                for gr in sum_gst.records:
                    if gr.match_status != MatchStatusEnum.MATCHED:
                        excs.append(ExceptionItem(
                            analysis_run_id=r_id, dataset_id=ds_id, analytic_id="GST_2B_MATCHING_EXCEPTION",
                            severity="High", title=f"GST Mismatch: {gr.match_status.value}",
                            description=f"Invoice {gr.invoice_number} ({gr.vendor_name} - {gr.vendor_gstin}): {gr.discrepancy_rationale}",
                            computed_evidence=f"Books Tax: ₹{gr.books_tax_paise / 100:,.2f} | 2B Tax: ₹{gr.gstr2b_tax_paise / 100:,.2f}",
                        ))
            elif r_type == "FIXED_ASSETS":
                sum_fa = FixedAssetEngine.audit_fixed_asset_register(dto.engagement_id, dto.data.get("assets", []))
                for fr in sum_fa.records:

                    if fr.anomaly_type != AssetAnomalyTypeEnum.CLEAN_ASSET:
                        excs.append(ExceptionItem(
                            analysis_run_id=r_id, dataset_id=ds_id, analytic_id="FIXED_ASSET_REGISTER_EXCEPTION",
                            severity="High", title=f"Fixed Asset Anomaly: {fr.anomaly_type.value}",
                            description=f"Asset Tag: {fr.asset_tag} ({fr.asset_name}), {fr.caro_disclosure_remark}",
                            computed_evidence=f"Gross: ₹{fr.gross_block_paise / 100:,.2f} | NBV: ₹{fr.net_book_value_paise / 100:,.2f}",
                        ))

            if excs:
                repo.add_exceptions(excs)
                AuditEventRepository(session).add(AuditEvent(
                    engagement_id=dto.engagement_id, actor="Reconciliation Engine",
                    action=f"Reconciliation Executed ({r_type})", details=f"Flagged {len(excs)} reconciliation exceptions.",
                ))
        return excs

    def create_audit_work(self, dto: CreateAuditWorkDTO) -> dict[str, Any]:
        """Convert an analytics anomaly or reconciliation difference into complete, interconnected audit work."""
        matrix_service = AuditMatrixService(self.db_manager)
        wp_service = WorkingPaperService(self.db_manager)

        sev = RiskSeverityEnum.HIGH if dto.severity.upper() == "HIGH" else RiskSeverityEnum.MEDIUM
        risk = matrix_service.create_risk(CreateRiskDTO(
            engagement_id=dto.engagement_id,
            risk_code=f"RSK-{uuid4().hex[:4].upper()}",
            category=dto.audit_area,
            title=f"Risk: {dto.title}",
            description=f"Risk in {dto.audit_area}: {dto.title}",
            inherent_risk=sev,
            control_risk=RiskSeverityEnum.MEDIUM,
            severity=sev,
        ))

        ast_val = str(dto.assertion).lower()
        if "occur" in ast_val:
            ast_enum = AssertionEnum.OCCURRENCE
        elif "accur" in ast_val or "measure" in ast_val:
            ast_enum = AssertionEnum.ACCURACY
        elif "exist" in ast_val:
            ast_enum = AssertionEnum.EXISTENCE
        elif "cut" in ast_val:
            ast_enum = AssertionEnum.CUT_OFF
        elif "val" in ast_val:
            ast_enum = AssertionEnum.VALUATION
        elif "right" in ast_val:
            ast_enum = AssertionEnum.RIGHTS_AND_OBLIGATIONS
        elif "class" in ast_val:
            ast_enum = AssertionEnum.CLASSIFICATION
        elif "present" in ast_val:
            ast_enum = AssertionEnum.PRESENTATION
        else:
            ast_enum = AssertionEnum.COMPLETENESS

        pop_str = f"Dataset {dto.dataset_id} ({len(dto.implicated_rows)} items)" if dto.implicated_rows else f"Dataset {dto.dataset_id}"
        proc = matrix_service.create_procedure(CreateProcedureDTO(
            engagement_id=dto.engagement_id,
            risk_id=risk.id,
            procedure_code=f"PRC-{uuid4().hex[:4].upper()}",
            objective=dto.objective or f"Verify accuracy and occurrence of {dto.audit_area} records.",
            procedure_type="Substantive Test",
            evidence_requirement=dto.computed_evidence or "Transaction vouchers and invoices",
            account_area=dto.audit_area,
            population=pop_str,
            methodology=dto.rule_or_analytic_id,
            assertion=ast_enum,
        ))


        wp = wp_service.create_working_paper(CreateWorkingPaperDTO(
            engagement_id=dto.engagement_id,
            index_reference=f"WP-FIN-{uuid4().hex[:6].upper()}",
            title=f"Testing Working Paper: {dto.title}",
            area=dto.audit_area,
            preparer_id=dto.preparer,
            procedure_ids=[proc.id],
        ))


        exc_entity = AuditException(
            source=dto.source, rule=dto.rule_or_analytic_id, evidence_ref=f"Dataset:{dto.dataset_id}",
            severity=dto.severity, status="OPEN", explanation=dto.description,
        )
        test_exec = TestExecution(
            procedure_id=proc.id, population=pop_str, sample_size=len(dto.implicated_rows),
            sample_refs=[str(r) for r in dto.implicated_rows], tester=dto.preparer,
            methodology_version="1.0.0", result="EXCEPTION_IDENTIFIED", exceptions=[exc_entity],
        )

        evidence = matrix_service.attach_evidence(AttachEvidenceDTO(
            engagement_id=dto.engagement_id,
            procedure_id=proc.id,
            dataset_id=dto.dataset_id,
            title=f"Evidence: {dto.title}",
            excerpt_or_reference=dto.computed_evidence or dto.description,
        ))
        evidence.working_paper_id = wp.id

        finding = matrix_service.create_finding(CreateFindingDTO(
            engagement_id=dto.engagement_id,
            procedure_id=proc.id,
            risk_id=risk.id,
            title=dto.title,
            description=dto.description,
            severity=sev,
            assertion=AssertionEnum.ACCURACY,
            preparer=dto.preparer,
        ))
        finding.working_paper_id = wp.id
        finding.linked_exception_ids = [exc_entity.id]
        finding.evidence_ids = [evidence.id]
        matrix_service.link_evidence_to_finding(finding.id, evidence.id)

        wp_service.add_link(wp.id, "PROCEDURE", proc.id)
        wp_service.add_link(wp.id, "FINDING", finding.id)
        wp_service.add_link(wp.id, "EVIDENCE", evidence.id)

        return {
            "risk": risk, "procedure": proc, "working_paper": wp,
            "test_execution": test_exec, "exception": exc_entity,
            "finding": finding, "evidence": evidence,
        }

    def list_exceptions_for_dataset(self, dataset_id: str) -> list[ExceptionItem]:
        with self.db_manager.session_scope() as session:
            return FinancialDataRepository(session).list_exceptions_by_dataset(dataset_id)

    def promote_exception_to_finding(
        self, exception_id: str, preparer: str = "Senior Auditor"
    ) -> Finding:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            from finauditpro.infrastructure.persistence.models import ExceptionItemModel

            exc_model = session.get(ExceptionItemModel, exception_id)
            if not exc_model:
                raise EntityNotFoundError("Exception Item", exception_id)
            exc_model.status = ExceptionStatusEnum.ACCEPTED.value
            ds = repo.get_dataset_by_id(exc_model.dataset_id) if exc_model.dataset_id else None
            eng_id = ds.engagement_id if ds else ""
            finding = repo.add_finding(Finding(
                engagement_id=eng_id, title=exc_model.title,
                description=f"{exc_model.description}\nEvidence: {exc_model.computed_evidence}",
                category="Substantive Audit Exception", severity=exc_model.severity,
                source="Deterministic Analytics Engine", preparer=preparer,
            ))
            AuditEventRepository(session).add(AuditEvent(
                engagement_id=eng_id, actor=preparer, action="Exception Promoted to Finding",
                details=f"Promoted analytics exception '{exc_model.title}' to formal finding.",
            ))
            return finding

    def list_findings_for_engagement(self, engagement_id: str) -> list[Finding]:
        with self.db_manager.session_scope() as session:
            return FinancialDataRepository(session).list_findings_by_engagement(engagement_id)
