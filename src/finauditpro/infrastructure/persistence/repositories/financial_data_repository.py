"""Repository managing Financial Datasets, Typed Rows, Analytics Exceptions, and Findings."""

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.financial_entities import (
    BankTransaction,
    DatasetStatusEnum,
    DatasetTypeEnum,
    ExceptionItem,
    ExceptionStatusEnum,
    FinancialDataset,
    FinancialRecord,
    Finding,
    FlaggedAnomaly,
    LedgerEntry,
    TrialBalanceLine,
)
from finauditpro.infrastructure.persistence.models import (
    BankTransactionModel,
    ExceptionItemModel,
    FinancialDatasetModel,
    FindingModel,
    LedgerEntryModel,
    TrialBalanceLineModel,
)


class FinancialDataRepository:
    """Repository managing dataset ingestion records, typed rows, analytics exceptions, and findings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_dataset_entity(self, model: FinancialDatasetModel) -> FinancialDataset:
        return FinancialDataset(
            id=model.id,
            engagement_id=model.engagement_id,
            dataset_name=model.dataset_name,
            dataset_type=DatasetTypeEnum(model.dataset_type)
            if model.dataset_type in DatasetTypeEnum._value2member_map_
            else DatasetTypeEnum.GENERAL_LEDGER,
            filename=model.dataset_name,
            content_hash=model.content_hash,
            stored_path=model.file_path,
            status=DatasetStatusEnum.IMPORTED,
            total_rows=model.row_count,
            row_count=model.row_count,
            error_rows=0,
            column_mappings=model.column_mappings,
            errors=[],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add_dataset(self, dataset: FinancialDataset) -> FinancialDataset:
        model = FinancialDatasetModel(
            id=dataset.id,
            engagement_id=dataset.engagement_id,
            dataset_name=dataset.dataset_name,
            dataset_type=dataset.dataset_type.value
            if hasattr(dataset.dataset_type, "value")
            else str(dataset.dataset_type),
            version=1,
            file_path=dataset.stored_path,
            content_hash=dataset.content_hash,
            row_count=dataset.row_count,
            column_mappings_json=json.dumps(dataset.column_mappings),
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_dataset_entity(model)

    def get_dataset_by_id(self, dataset_id: str) -> FinancialDataset | None:
        model = self.session.get(FinancialDatasetModel, dataset_id)
        return self._to_dataset_entity(model) if model else None

    def get_dataset(self, dataset_id: str) -> FinancialDataset | None:
        return self.get_dataset_by_id(dataset_id)

    def add_records(self, records: list[FinancialRecord]) -> None:
        entries = [
            LedgerEntry(
                id=r.id,
                dataset_id=r.dataset_id,
                source_row_no=r.row_index,
                entry_date=r.date,
                voucher_number=r.transaction_id or r.invoice_number,
                account_code=r.account_code,
                account_name=r.account_name,
                debit_paise=int(round(r.debit * 100)),
                credit_paise=int(round(r.credit * 100)),
                narration=r.narration,
            )
            for r in records
        ]
        self.add_ledger_entries(entries)

    def list_datasets_by_engagement(self, engagement_id: str) -> list[FinancialDataset]:
        stmt = (
            select(FinancialDatasetModel)
            .where(FinancialDatasetModel.engagement_id == engagement_id)
            .order_by(FinancialDatasetModel.created_at.desc())
        )
        return [self._to_dataset_entity(m) for m in self.session.scalars(stmt).all()]

    def get_datasets_by_engagement(self, engagement_id: str) -> list[FinancialDataset]:
        return self.list_datasets_by_engagement(engagement_id)

    def get_records_by_dataset(self, dataset_id: str) -> list[FinancialRecord]:
        return [
            FinancialRecord(
                id=e.id,
                dataset_id=e.dataset_id,
                row_index=e.source_row_no,
                transaction_id=e.voucher_number,
                date=e.entry_date,
                account_code=e.account_code,
                account_name=e.account_name,
                debit=e.debit_paise / 100.0,
                credit=e.credit_paise / 100.0,
                amount=(e.debit_paise - e.credit_paise) / 100.0,
                narration=e.narration,
            )
            for e in self.get_ledger_entries(dataset_id)
        ]

    def get_dataset_records(self, dataset_id: str) -> list[FinancialRecord]:
        return self.get_records_by_dataset(dataset_id)

    def add_analytics_result(self, result: Any, anomalies: list[Any]) -> Any:
        exc_items = [
            ExceptionItem(
                analysis_run_id=getattr(result, "id", str(uuid4())),
                dataset_id=getattr(result, "dataset_id", ""),
                analytic_id=str(getattr(result, "analysis_type", "legacy")),
                severity=getattr(a, "severity", "Medium"),
                title=f"Anomaly at Row {getattr(a, 'row_index', 1)}",
                description=getattr(a, "rationale", ""),
                implicated_rows=[getattr(a, "row_index", 1)],
                computed_evidence=getattr(a, "rationale", ""),
            )
            for a in anomalies
        ]
        self.add_exceptions(exc_items)
        return result

    def list_analytics_results_for_engagement(self, engagement_id: str) -> list[Any]:
        results = []
        for ds in self.list_datasets_by_engagement(engagement_id):
            results.extend(self.list_exceptions_by_dataset(ds.id))
        return results

    def list_flagged_anomalies_for_engagement(self, engagement_id: str) -> list[Any]:
        anomalies = []
        for ds in self.list_datasets_by_engagement(engagement_id):
            for e in self.list_exceptions_by_dataset(ds.id):
                anomalies.append(
                    FlaggedAnomaly(
                        analytics_result_id=e.analysis_run_id,
                        dataset_id=ds.id,
                        row_index=e.implicated_rows[0] if e.implicated_rows else 1,
                        transaction_id=None,
                        date=None,
                        amount=0.0,
                        account_name=None,
                        rationale=e.computed_evidence or e.description,
                        severity=e.severity,
                    )
                )
        return anomalies

    def add_ledger_entries(self, entries: list[LedgerEntry]) -> None:
        models = [
            LedgerEntryModel(
                id=e.id,
                dataset_id=e.dataset_id,
                source_row_no=e.source_row_no,
                entry_date=e.entry_date,
                voucher_type=e.voucher_type,
                voucher_number=e.voucher_number,
                account_code=e.account_code,
                account_name=e.account_name,
                debit_paise=e.debit_paise,
                credit_paise=e.credit_paise,
                narration=e.narration,
                reference=e.reference,
                created_by_raw=e.created_by_raw,
                raw_values_json=json.dumps(e.raw_values),
            )
            for e in entries
        ]
        self.session.add_all(models)
        self.session.flush()

    def get_ledger_entries(self, dataset_id: str) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntryModel)
            .where(LedgerEntryModel.dataset_id == dataset_id)
            .order_by(LedgerEntryModel.source_row_no.asc())
        )
        return [
            LedgerEntry(
                id=m.id,
                dataset_id=m.dataset_id,
                source_row_no=m.source_row_no,
                entry_date=m.entry_date,
                voucher_type=m.voucher_type,
                voucher_number=m.voucher_number,
                account_code=m.account_code,
                account_name=m.account_name,
                debit_paise=m.debit_paise,
                credit_paise=m.credit_paise,
                narration=m.narration,
                reference=m.reference,
                created_by_raw=m.created_by_raw,
                raw_values=json.loads(m.raw_values_json) if m.raw_values_json else {},
            )
            for m in self.session.scalars(stmt).all()
        ]

    def add_trial_balance_lines(self, lines: list[TrialBalanceLine]) -> None:
        models = [
            TrialBalanceLineModel(
                id=l.id,
                dataset_id=l.dataset_id,
                source_row_no=l.source_row_no,
                account_code=l.account_code,
                account_name=l.account_name,
                account_type=l.account_type,
                opening_dr_paise=l.opening_dr_paise,
                opening_cr_paise=l.opening_cr_paise,
                debit_paise=l.debit_paise,
                credit_paise=l.credit_paise,
                closing_dr_paise=l.closing_dr_paise,
                closing_cr_paise=l.closing_cr_paise,
                raw_values_json=json.dumps(l.raw_values),
            )
            for l in lines
        ]
        self.session.add_all(models)
        self.session.flush()

    def get_trial_balance_lines(self, dataset_id: str) -> list[TrialBalanceLine]:
        stmt = (
            select(TrialBalanceLineModel)
            .where(TrialBalanceLineModel.dataset_id == dataset_id)
            .order_by(TrialBalanceLineModel.source_row_no.asc())
        )
        return [
            TrialBalanceLine(
                id=m.id,
                dataset_id=m.dataset_id,
                source_row_no=m.source_row_no,
                account_code=m.account_code,
                account_name=m.account_name,
                account_type=m.account_type,
                opening_dr_paise=m.opening_dr_paise,
                opening_cr_paise=m.opening_cr_paise,
                debit_paise=m.debit_paise,
                credit_paise=m.credit_paise,
                closing_dr_paise=m.closing_dr_paise,
                closing_cr_paise=m.closing_cr_paise,
                raw_values=json.loads(m.raw_values_json) if m.raw_values_json else {},
            )
            for m in self.session.scalars(stmt).all()
        ]

    def add_bank_transactions(self, txns: list[BankTransaction]) -> None:
        models = [
            BankTransactionModel(
                id=t.id,
                dataset_id=t.dataset_id,
                source_row_no=t.source_row_no,
                txn_date=t.txn_date,
                value_date=t.value_date,
                txn_id=t.txn_id,
                description=t.description,
                debit_paise=t.debit_paise,
                credit_paise=t.credit_paise,
                balance_paise=t.balance_paise,
                reference=t.reference,
                raw_values_json=json.dumps(t.raw_values),
            )
            for t in txns
        ]
        self.session.add_all(models)
        self.session.flush()

    def get_bank_transactions(self, dataset_id: str) -> list[BankTransaction]:
        stmt = (
            select(BankTransactionModel)
            .where(BankTransactionModel.dataset_id == dataset_id)
            .order_by(BankTransactionModel.source_row_no.asc())
        )
        return [
            BankTransaction(
                id=m.id,
                dataset_id=m.dataset_id,
                source_row_no=m.source_row_no,
                txn_date=m.txn_date,
                value_date=m.value_date,
                txn_id=m.txn_id,
                description=m.description,
                debit_paise=m.debit_paise,
                credit_paise=m.credit_paise,
                balance_paise=m.balance_paise,
                reference=m.reference,
                raw_values=json.loads(m.raw_values_json) if m.raw_values_json else {},
            )
            for m in self.session.scalars(stmt).all()
        ]

    def add_exceptions(self, exceptions: list[ExceptionItem]) -> None:
        models = [
            ExceptionItemModel(
                id=e.id,
                analysis_run_id=e.analysis_run_id,
                dataset_id=e.dataset_id,
                analytic_id=e.analytic_id,
                severity=e.severity,
                title=e.title,
                description=e.description,
                implicated_rows_json=json.dumps(e.implicated_rows),
                computed_evidence=e.computed_evidence,
                status=e.status.value if hasattr(e.status, "value") else str(e.status),
                reviewer=e.reviewer,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in exceptions
        ]
        self.session.add_all(models)
        self.session.flush()

    def list_exceptions_by_dataset(self, dataset_id: str) -> list[ExceptionItem]:
        stmt = (
            select(ExceptionItemModel)
            .where(ExceptionItemModel.dataset_id == dataset_id)
            .order_by(ExceptionItemModel.created_at.desc())
        )
        return [
            ExceptionItem(
                id=m.id,
                analysis_run_id=m.analysis_run_id,
                dataset_id=m.dataset_id,
                analytic_id=m.analytic_id,
                severity=m.severity,
                title=m.title,
                description=m.description,
                implicated_rows=json.loads(m.implicated_rows_json)
                if m.implicated_rows_json
                else [],
                computed_evidence=m.computed_evidence,
                status=ExceptionStatusEnum(m.status)
                if m.status in ExceptionStatusEnum._value2member_map_
                else ExceptionStatusEnum.OPEN,
                reviewer=m.reviewer,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in self.session.scalars(stmt).all()
        ]

    def add_finding(self, finding: Finding) -> Finding:
        model = FindingModel(
            id=finding.id,
            engagement_id=finding.engagement_id,
            title=finding.title,
            description=finding.description,
            category=finding.category,
            severity=finding.severity,
            amount_paise=finding.amount_paise,
            affected_account=finding.affected_account,
            source=finding.source,
            ai_generated=finding.ai_generated,
            status=finding.status,
            preparer=finding.preparer,
            reviewer=finding.reviewer,
            created_at=finding.created_at,
            updated_at=finding.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return finding

    def list_findings_by_engagement(self, engagement_id: str) -> list[Finding]:
        stmt = (
            select(FindingModel)
            .where(FindingModel.engagement_id == engagement_id)
            .order_by(FindingModel.created_at.desc())
        )
        return [
            Finding(
                id=m.id,
                engagement_id=m.engagement_id,
                title=m.title,
                description=m.description,
                category=m.category,
                severity=m.severity,
                amount_paise=m.amount_paise,
                affected_account=m.affected_account,
                source=m.source,
                ai_generated=m.is_ai_generated,
                status=m.status,
                preparer=m.preparer,
                reviewer=m.reviewer,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in self.session.scalars(stmt).all()
        ]
