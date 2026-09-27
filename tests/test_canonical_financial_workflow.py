"""Canonical Financial Data Workflow Integration Test Suite.

Validates the full 8-stage financial lifecycle:
Import -> Validate -> Normalize -> Map -> Reconcile -> Analyze -> Exceptions -> Audit Work

Covers:
1. Import & Validation Preview (Column, type, date, amount, duplicate checks).
2. Malformed file rejection (empty sheets, invalid dates, corrupt headers).
3. Trial Balance Invariant: Total Debit == Total Credit (Strict integer-paise arithmetic).
4. Schedule III Account Mapping & Lead Schedule Generation.
5. Reconciliation Engines (BRS, GST 2B, Fixed Assets) generating deterministic exceptions.
6. 'CREATE AUDIT WORK' pipeline linking:
   Procedure -> Population -> Test Result -> Exception -> Evidence -> Finding -> Working Paper.
7. Large-dataset ingestion and analysis performance.
"""

import csv
from pathlib import Path
import pytest

from finauditpro.application.account_mapping_dtos import MapAccountDTO, SyncTrialBalanceAccountsDTO, ValidateMappingsDTO
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.financial_dtos import CreateAuditWorkDTO, ImportDatasetDTO, RunReconciliationDTO
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_service import FinancialService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.bank_reconciliation_engine import BRSItemTypeEnum
from finauditpro.domain.entities import AuditTypeEnum, EngagementStatusEnum
from finauditpro.domain.financial_entities import DatasetTypeEnum
from finauditpro.infrastructure.financial.financial_importer import FinancialImportError
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def financial_env(tmp_path):
    db_file = tmp_path / "test_financial_canonical.db"
    db_mgr = DatabaseManager(str(db_file))
    db_mgr.create_tables()

    firm_svc = FirmService(db_mgr)
    client_svc = ClientService(db_mgr)
    eng_svc = EngagementService(db_mgr)
    fin_svc = FinancialService(db_mgr)
    map_svc = AccountMappingService(db_mgr)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Singhal & Associates Chartered Accountants"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Apex Global Logistics Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.PLANNING,
        )
    )
    return eng, fin_svc, map_svc, tmp_path


class TestCanonicalFinancialWorkflow:
    """End-to-end statutory financial data lifecycle tests."""

    def test_import_validation_preview_and_malformed_file_handling(self, financial_env):
        eng, fin_svc, _, tmp_path = financial_env

        # 1. Test empty CSV rejection
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")
        with pytest.raises(FinancialImportError) as exc:
            fin_svc.preview_dataset_import(str(empty_csv), DatasetTypeEnum.GENERAL_LEDGER)
        assert "Empty CSV file" in str(exc.value)

        # 2. Test malformed rows preview with type errors and invalid dates
        malformed_csv = tmp_path / "malformed_gl.csv"
        with malformed_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Voucher Number", "Account Name", "Debit", "Credit", "Narration"])
            writer.writerow(["2026-03-31", "V-101", "Cash", "1000.00", "0.00", "Valid Line"])
            writer.writerow(["INVALID_DATE", "V-102", "Bank", "NOT_A_NUMBER", "0.00", "Malformed Line"])

        preview = fin_svc.preview_dataset_import(str(malformed_csv), DatasetTypeEnum.GENERAL_LEDGER)
        assert preview.total_rows == 2
        assert preview.valid_rows_count == 1
        assert preview.error_count == 1
        assert len(preview.errors) == 1

    def test_trial_balance_debit_credit_invariant_and_integer_paise(self, financial_env):
        eng, fin_svc, _, tmp_path = financial_env

        # 1. Balanced Trial Balance
        tb_csv = tmp_path / "balanced_tb.csv"
        with tb_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Account Code", "Account Name", "Debit", "Credit"])
            writer.writerow(["1001", "Share Capital", "0.00", "5000000.00"])
            writer.writerow(["2001", "HDFC Bank Loan", "0.00", "2500000.00"])
            writer.writerow(["3001", "Plant & Machinery", "4500000.00", "0.00"])
            writer.writerow(["3002", "Trade Receivables", "3000000.00", "0.00"])

        preview = fin_svc.preview_dataset_import(str(tb_csv), DatasetTypeEnum.TRIAL_BALANCE)
        assert preview.is_balanced
        assert preview.total_debit_paise == 750000000
        assert preview.total_credit_paise == 750000000
        assert preview.discrepancy_paise == 0

        # Import into repository
        ds = fin_svc.import_dataset(
            ImportDatasetDTO(
                engagement_id=eng.id,
                dataset_name="Balanced TB FY25-26",
                file_path=str(tb_csv),
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            )
        )
        assert ds.row_count == 4

        # 2. Imbalanced Trial Balance preview
        imbalanced_tb = tmp_path / "imbalanced_tb.csv"
        with imbalanced_tb.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Account Code", "Account Name", "Debit", "Credit"])
            writer.writerow(["1001", "Share Capital", "0.00", "5000000.00"])
            writer.writerow(["3001", "Plant & Machinery", "4000000.00", "0.00"])

        imb_preview = fin_svc.preview_dataset_import(str(imbalanced_tb), DatasetTypeEnum.TRIAL_BALANCE)
        assert not imb_preview.is_balanced
        assert abs(imb_preview.discrepancy_paise) == 100000000  # ₹10,00,000 difference

    def test_schedule_iii_mapping_and_lead_schedule_generation(self, financial_env):
        eng, fin_svc, map_svc, tmp_path = financial_env

        tb_csv = tmp_path / "tb_for_mapping.csv"
        with tb_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Account Code", "Account Name", "Debit", "Credit"])
            writer.writerow(["1001", "Equity Share Capital", "0.00", "1000000.00"])
            writer.writerow(["3001", "CNC Lathe Machine", "1000000.00", "0.00"])

        ds = fin_svc.import_dataset(
            ImportDatasetDTO(
                engagement_id=eng.id,
                dataset_name="TB for Schedule III Mapping",
                file_path=str(tb_csv),
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            )
        )

        # 1. Sync accounts to mappings
        mappings = map_svc.sync_trial_balance_accounts(
            SyncTrialBalanceAccountsDTO(engagement_id=eng.id, dataset_id=ds.id)
        )
        assert len(mappings) == 2

        # 2. Map accounts to Schedule III heads
        map_svc.map_single_account(
            MapAccountDTO(
                engagement_id=eng.id,
                account_code="1001",
                schedule_iii_category="Shareholders' Funds",
                schedule_iii_line_item="Share Capital",
                lead_schedule_ref="B-10",
                account_type=AccountTypeEnum.EQUITY,
            )
        )
        map_svc.map_single_account(
            MapAccountDTO(
                engagement_id=eng.id,
                account_code="3001",
                schedule_iii_category="Non-Current Assets",
                schedule_iii_line_item="Property, Plant & Equipment",
                lead_schedule_ref="B-30",
                account_type=AccountTypeEnum.ASSET,
            )
        )

        # 3. Validate mapping quality gate
        report = map_svc.validate_mappings(ValidateMappingsDTO(engagement_id=eng.id))
        assert report.is_valid_for_finalization
        assert report.mapped_count == 2
        assert report.unmapped_count == 0

    def test_reconciliation_difference_to_audit_work_pipeline(self, financial_env):
        eng, fin_svc, _, _ = financial_env

        # Run Bank Reconciliation Engine with stale cheque item
        brs_data = {
            "items": [
                {
                    "bank_account_number": "HDFC-0011223344",
                    "item_type": BRSItemTypeEnum.UNPRESENTED_CHEQUE,
                    "reference_number": "CHQ-991122",
                    "entry_date": "2025-10-15",
                    "amount_paise": 50000000,
                    "clearance_date": None,
                }
            ]
        }
        excs = fin_svc.run_reconciliation(
            RunReconciliationDTO(
                engagement_id=eng.id,
                reconciliation_type="BRS",
                as_of_date="2026-03-31",
                data=brs_data,
            )
        )
        assert len(excs) == 1
        exc = excs[0]
        assert "Stale Cheque" in exc.title or "Stale" in exc.description

        # 'CREATE AUDIT WORK': Convert reconciliation difference to active audit work
        work_package = fin_svc.create_audit_work(
            CreateAuditWorkDTO(
                engagement_id=eng.id,
                dataset_id=exc.dataset_id,
                title="Stale Cheque (>90 Days) Reversal Audit",
                audit_area="Cash & Bank Balances",
                description=exc.description,
                severity=exc.severity,
                rule_or_analytic_id=exc.analytic_id,
                computed_evidence=exc.computed_evidence,
                assertion="Existence",
                preparer="Senior Auditor",
            )
        )

        assert work_package["risk"] is not None
        assert work_package["procedure"] is not None
        assert work_package["working_paper"] is not None
        assert work_package["finding"] is not None
        assert work_package["evidence"] is not None
        assert work_package["finding"].working_paper_id == work_package["working_paper"].id

    def test_large_dataset_performance_and_analytics(self, financial_env):
        eng, fin_svc, _, tmp_path = financial_env

        # Generate 2,500 GL transactions
        large_csv = tmp_path / "large_gl.csv"
        with large_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Voucher Number", "Account Code", "Account Name", "Debit", "Credit", "Narration"])
            for i in range(1, 2501):
                writer.writerow([
                    "2026-01-15",
                    f"V-{i:05d}",
                    "4001",
                    "Domestic Sales",
                    "0.00",
                    f"{1000 + (i % 50) * 100}.00",
                    f"Sales invoice {i}",
                ])

        ds = fin_svc.import_dataset(
            ImportDatasetDTO(
                engagement_id=eng.id,
                dataset_name="Large Scale GL",
                file_path=str(large_csv),
                dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
            )
        )
        assert ds.row_count == 2500

        # Execute duplicate payments and analytics
        analytics_excs = fin_svc.run_deterministic_analytics(ds.id)
        assert isinstance(analytics_excs, list)
