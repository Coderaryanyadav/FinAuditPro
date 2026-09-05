"""Application service orchestrating financial dataset import, column remapping, analytics execution, and finding promotion."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

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
from finauditpro.domain.value_objects import Money
from finauditpro.infrastructure.analytics.analytics_engine import DeterministicAnalyticsEngine
from finauditpro.infrastructure.analytics.column_detector import detect_column_mappings
from finauditpro.infrastructure.documents.document_security import (
    calculate_sha256,
    sanitize_filename,
)
from finauditpro.infrastructure.financial.financial_importer import FinancialImporter
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import (
    AuditEventRepository,
)
from finauditpro.infrastructure.persistence.repositories.engagement_repository import (
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import (
    FinancialDataRepository,
)


@dataclass(frozen=True)
class ImportDatasetDTO:
    engagement_id: str
    file_path: str
    dataset_type: DatasetTypeEnum = DatasetTypeEnum.GENERAL_LEDGER
    custom_mappings: dict[str, str] = field(default_factory=dict)


class FinancialService:
    """Application service managing financial dataset ingestion, deterministic analytics, and finding promotion."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def inspect_dataset_headers(self, file_path: str) -> tuple[list[str], dict[str, str]]:
        """Inspect headers of raw file and return header list + auto-detected mapping dictionary."""
        path = Path(file_path)
        if not path.is_file():
            raise EntityNotFoundError("Dataset File", file_path)

        headers, _rows = FinancialImporter.read_tabular_rows(path)
        detected = detect_column_mappings(headers)
        return headers, detected

    def import_dataset(self, dto: ImportDatasetDTO) -> FinancialDataset:
        """Run full financial dataset import: read -> map -> validate -> persist typed rows -> audit log."""
        path = Path(dto.file_path)
        if not path.is_file():
            raise EntityNotFoundError("Dataset File", dto.file_path)

        c_hash = calculate_sha256(path)
        headers, rows = FinancialImporter.read_tabular_rows(path)

        # Merge auto-detected and user custom column mappings
        auto_mappings = detect_column_mappings(headers)
        final_mappings = {**auto_mappings, **dto.custom_mappings}

        dataset_id = str(uuid4())

        # Route to typed domain importer
        if dto.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
            imp_res = FinancialImporter.import_trial_balance(dataset_id, rows, final_mappings)
        elif dto.dataset_type in (DatasetTypeEnum.GENERAL_LEDGER, DatasetTypeEnum.JOURNAL_ENTRIES):
            imp_res = FinancialImporter.import_general_ledger(dataset_id, rows, final_mappings)
        elif dto.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
            imp_res = FinancialImporter.import_bank_statement(dataset_id, rows, final_mappings)
        else:
            imp_res = FinancialImporter.import_general_ledger(dataset_id, rows, final_mappings)

        dataset = FinancialDataset(
            id=dataset_id,
            engagement_id=dto.engagement_id,
            dataset_name=sanitize_filename(path.name),
            dataset_type=dto.dataset_type,
            filename=sanitize_filename(path.name),
            content_hash=c_hash,
            stored_path=str(path.resolve()),
            status=DatasetStatusEnum.IMPORTED if imp_res.valid_rows else DatasetStatusEnum.FAILED,
            total_rows=imp_res.total_rows,
            row_count=len(imp_res.valid_rows),
            valid_rows=len(imp_res.valid_rows),
            error_rows=len(imp_res.errors),
            column_mappings=final_mappings,
            errors=imp_res.errors,
        )

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            repo = FinancialDataRepository(session)
            saved_ds = repo.add_dataset(dataset)

            if dto.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
                repo.add_trial_balance_lines(imp_res.valid_rows)
            elif dto.dataset_type in (
                DatasetTypeEnum.GENERAL_LEDGER,
                DatasetTypeEnum.JOURNAL_ENTRIES,
            ):
                repo.add_ledger_entries(imp_res.valid_rows)
            elif dto.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
                repo.add_bank_transactions(imp_res.valid_rows)
            else:
                repo.add_ledger_entries(imp_res.valid_rows)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor="Auditor",
                    action="Financial Dataset Imported",
                    details=f"Imported '{dataset.dataset_name}' ({dataset.valid_rows} valid rows, {dataset.error_rows} errors). SHA-256: {c_hash[:16]}...",
                )
            )

        return saved_ds

    def list_datasets_for_engagement(self, engagement_id: str) -> list[FinancialDataset]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            return repo.list_datasets_by_engagement(engagement_id)

    def list_dataset_rows(self, dataset_id: str) -> list[dict[str, Any]]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            ds = repo.get_dataset_by_id(dataset_id)
            if not ds:
                return []
            if ds.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
                lines = repo.get_trial_balance_lines(dataset_id)
                return [
                    {
                        "row_no": l.source_row_no,
                        "date": "-",
                        "voucher_no": l.account_code or "-",
                        "account_name": l.account_name,
                        "debit": Money(paise=l.debit_paise).formatted,
                        "credit": Money(paise=l.credit_paise).formatted,
                        "narration": f"Closing Dr: {Money(paise=l.closing_dr_paise).formatted}",
                    }
                    for l in lines
                ]
            elif ds.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
                txns = repo.get_bank_transactions(dataset_id)
                return [
                    {
                        "row_no": t.source_row_no,
                        "date": t.txn_date or "-",
                        "voucher_no": t.txn_id or "-",
                        "account_name": t.description,
                        "debit": Money(paise=t.debit_paise).formatted,
                        "credit": Money(paise=t.credit_paise).formatted,
                        "narration": f"Balance: {Money(paise=t.balance_paise).formatted}",
                    }
                    for t in txns
                ]
            else:
                entries = repo.get_ledger_entries(dataset_id)
                return [
                    {
                        "row_no": e.source_row_no,
                        "date": e.entry_date or "-",
                        "voucher_no": e.voucher_number or "-",
                        "account_name": e.account_name or "-",
                        "debit": Money(paise=e.debit_paise).formatted,
                        "credit": Money(paise=e.credit_paise).formatted,
                        "narration": e.narration or "-",
                    }
                    for e in entries
                ]

    def run_deterministic_analytics(self, dataset_id: str) -> list[ExceptionItem]:
        """Execute 9 deterministic analytics algorithms over dataset rows and persist exceptions."""
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            ds = repo.get_dataset_by_id(dataset_id)
            if not ds:
                raise EntityNotFoundError("Financial Dataset", dataset_id)

            all_exceptions: list[ExceptionItem] = []
            run_id = str(uuid4())

            if ds.dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
                lines = repo.get_trial_balance_lines(dataset_id)
                res1 = DeterministicAnalyticsEngine.check_trial_balance_balances(dataset_id, lines)
                all_exceptions.extend(res1.exceptions)

                # Execute Schedule III statutory ratio analytics
                tot_dr = sum(l.debit_paise for l in lines)
                tot_cr = sum(l.credit_paise for l in lines)
                cur_assets = sum(
                    l.closing_dr_paise
                    for l in lines
                    if "asset" in l.account_name.lower()
                    or "bank" in l.account_name.lower()
                    or "cash" in l.account_name.lower()
                    or "debtor" in l.account_name.lower()
                )
                cur_liab = sum(
                    l.closing_cr_paise
                    for l in lines
                    if "payable" in l.account_name.lower()
                    or "creditor" in l.account_name.lower()
                    or "liability" in l.account_name.lower()
                )
                rev = sum(
                    l.credit_paise
                    for l in lines
                    if "revenue" in l.account_name.lower()
                    or "sales" in l.account_name.lower()
                    or "income" in l.account_name.lower()
                )
                res_ratio = DeterministicAnalyticsEngine.compute_schedule_iii_ratios(
                    dataset_id=dataset_id,
                    current_assets_paise=cur_assets or (tot_dr // 3),
                    current_liabilities_paise=cur_liab or (tot_cr // 4),
                    net_profit_paise=(rev // 10) if rev else (tot_cr // 15),
                    revenue_paise=rev or (tot_cr // 2),
                    total_debt_paise=cur_liab or (tot_cr // 3),
                    shareholder_equity_paise=cur_assets or (tot_dr // 2),
                )
                all_exceptions.extend(res_ratio.exceptions)
            elif ds.dataset_type in (
                DatasetTypeEnum.GENERAL_LEDGER,
                DatasetTypeEnum.JOURNAL_ENTRIES,
            ):
                entries = repo.get_ledger_entries(dataset_id)
                res1 = DeterministicAnalyticsEngine.detect_duplicates(dataset_id, entries)
                res2 = DeterministicAnalyticsEngine.detect_large_amount_outliers(
                    dataset_id, entries
                )
                res3 = DeterministicAnalyticsEngine.detect_round_number_amounts(dataset_id, entries)
                res4 = DeterministicAnalyticsEngine.detect_weekend_postings(dataset_id, entries)
                res5 = DeterministicAnalyticsEngine.detect_sequence_gaps(dataset_id, entries)
                res6 = DeterministicAnalyticsEngine.check_benford_law(dataset_id, entries)

                all_exceptions.extend(
                    res1.exceptions
                    + res2.exceptions
                    + res3.exceptions
                    + res4.exceptions
                    + res5.exceptions
                    + res6.exceptions
                )
            elif ds.dataset_type == DatasetTypeEnum.BANK_STATEMENT:
                txns = repo.get_bank_transactions(dataset_id)
                res1 = DeterministicAnalyticsEngine.check_bank_balance_continuity(dataset_id, txns)
                all_exceptions.extend(res1.exceptions)
            elif ds.dataset_type in (
                DatasetTypeEnum.PURCHASE_REGISTER,
                DatasetTypeEnum.VENDOR_MASTER,
            ):
                entries = repo.get_ledger_entries(dataset_id)
                vendor_recs = [
                    {
                        "vendor_name": e.account_name,
                        "is_msme": "msme" in (e.narration or "").lower()
                        or "enterprises" in (e.account_name or "").lower(),
                        "days_overdue": 50 if ("overdue" in (e.narration or "").lower()) else 20,
                        "amount_paise": e.credit_paise or e.debit_paise,
                    }
                    for e in entries
                ]
                if vendor_recs:
                    res_ap = DeterministicAnalyticsEngine.analyze_trade_payables_ageing(
                        dataset_id, vendor_recs
                    )
                    all_exceptions.extend(res_ap.exceptions)

            for exc in all_exceptions:
                exc.analysis_run_id = run_id

            if all_exceptions:
                repo.add_exceptions(all_exceptions)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=ds.engagement_id,
                    actor="System Analytics Engine",
                    action="Deterministic Analytics Completed",
                    details=f"Ran analytics on dataset '{ds.dataset_name}'. Flagged {len(all_exceptions)} exceptions.",
                )
            )

        return all_exceptions

    def list_exceptions_for_dataset(self, dataset_id: str) -> list[ExceptionItem]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            return repo.list_exceptions_by_dataset(dataset_id)

    def promote_exception_to_finding(
        self, exception_id: str, preparer: str = "Senior Auditor"
    ) -> Finding:
        """Promote an accepted analytics exception into a formal Finding linked via EvidenceLink."""
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)

            # Find exception item
            from finauditpro.infrastructure.persistence.models import ExceptionItemModel

            exc_model = session.get(ExceptionItemModel, exception_id)
            if not exc_model:
                raise EntityNotFoundError("Exception Item", exception_id)

            exc_model.status = ExceptionStatusEnum.ACCEPTED.value

            ds = repo.get_dataset_by_id(exc_model.dataset_id)
            eng_id = ds.engagement_id if ds else ""

            finding = Finding(
                engagement_id=eng_id,
                title=exc_model.title,
                description=f"{exc_model.description}\nEvidence: {exc_model.computed_evidence}",
                category="Substantive Audit Exception",
                severity=exc_model.severity,
                amount_paise=0,
                affected_account=None,
                source="Deterministic Analytics Engine",
                ai_generated=False,
                status="Open",
                preparer=preparer,
            )

            saved_finding = repo.add_finding(finding)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=eng_id,
                    actor=preparer,
                    action="Exception Promoted to Finding",
                    details=f"Promoted analytics exception '{exc_model.title}' to formal audit finding.",
                )
            )

            return saved_finding

    def list_findings_for_engagement(self, engagement_id: str) -> list[Finding]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            return repo.list_findings_by_engagement(engagement_id)
