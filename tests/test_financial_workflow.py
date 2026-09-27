"""Comprehensive test suite for canonical financial-data workflow:
Import -> Validate -> Normalize -> Map -> Reconcile -> Analyze -> Exceptions -> Audit Work.
Includes large-dataset tests and malformed-file tests.
"""

import csv
from datetime import datetime
from pathlib import Path
import pytest

from finauditpro.application.account_mapping_dtos import MapAccountDTO, SyncTrialBalanceAccountsDTO
from finauditpro.application.financial_dtos import (
    CreateAuditWorkDTO,
    ImportDatasetDTO,
    RunReconciliationDTO,
)
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.financial_service import FinancialService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_matrix_entities import AssertionEnum
from finauditpro.domain.financial_entities import DatasetTypeEnum

from finauditpro.domain.value_objects import Money
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import Base, EngagementModel


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_fin_workflow.db"
    db_manager = DatabaseManager(f"sqlite:///{db_file}")
    with db_manager.engine.begin() as conn:
        Base.metadata.create_all(conn)

    # Seed firm, client, engagement
    from finauditpro.infrastructure.persistence.models import FirmModel, ClientModel
    with db_manager.session_scope() as session:
        firm = FirmModel(id="firm-01", name="S. K. & Associates", registration_number="FRN-123456")
        session.add(firm)
        client = ClientModel(id="client-01", firm_id="firm-01", name="Acme Enterprises Pvt Ltd", pan="AABCA1234F")
        session.add(client)
        eng = EngagementModel(
            id="eng-fin-101",
            firm_id="firm-01",
            client_id="client-01",
            financial_year="2025-2026",
            audit_type="Statutory Audit",
            status="FIELDWORK",
            partner="Partner CA",
        )
        session.add(eng)


    return db_manager


def test_validation_preview_and_import_trial_balance(test_db: DatabaseManager, tmp_path: Path):
    """Test validation preview, exact monetary balance enforcement, and normalized import."""
    tb_csv = tmp_path / "balanced_tb.csv"
    with tb_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Code", "Account Name", "Opening Dr", "Opening Cr", "Debit", "Credit", "Closing Dr", "Closing Cr"])
        writer.writerow(["1001", "Cash and Bank", "50,000.00", "0.00", "25,000.00", "10,000.00", "65,000.00", "0.00"])
        writer.writerow(["2001", "Trade Payables", "0.00", "50,000.00", "10,000.00", "25,000.00", "0.00", "65,000.00"])

    fin_service = FinancialService(test_db)
    
    # 1. Validation Preview
    preview = fin_service.preview_dataset_import(
        file_path=str(tb_csv),
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        custom_mappings={
            "account_code": "Account Code",
            "account_name": "Account Name",
            "opening_dr": "Opening Dr",
            "opening_cr": "Opening Cr",
            "debit": "Debit",
            "credit": "Credit",
            "closing_dr": "Closing Dr",
            "closing_cr": "Closing Cr",
        },
    )

    assert preview.validation_passed is True
    assert preview.total_rows == 2
    assert preview.valid_rows_count == 2
    assert preview.error_count == 0
    assert preview.is_balanced is True
    assert preview.total_debit_paise == 3500000  # ₹35,000.00
    assert preview.total_credit_paise == 3500000

    # 2. Ingest Dataset
    dataset = fin_service.import_dataset(
        ImportDatasetDTO(
            engagement_id="eng-fin-101",
            dataset_name="Balanced TB FY26",
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            file_path=str(tb_csv),
            column_mappings={
                "account_code": "Account Code",
                "account_name": "Account Name",
                "opening_dr": "Opening Dr",
                "opening_cr": "Opening Cr",
                "debit": "Debit",
                "credit": "Credit",
                "closing_dr": "Closing Dr",
                "closing_cr": "Closing Cr",
            },
        )
    )
    assert dataset.id is not None
    assert dataset.valid_rows == 2


def test_malformed_file_validation_and_unbalanced_tb(test_db: DatabaseManager, tmp_path: Path):
    """Test that validation preview catches unbalanced TB, invalid dates, corrupted amounts, and duplicate vouchers."""
    bad_csv = tmp_path / "bad_dataset.csv"
    with bad_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Voucher No", "Date", "Account Name", "Debit", "Credit"])
        writer.writerow(["V-001", "31/03/2026", "Sales Revenue", "invalid_amount", "0.00"])  # Corrupted amount
        writer.writerow(["V-002", "99/99/2026", "Office Rent", "10,000.00", "0.00"])         # Corrupted date
        writer.writerow(["V-001", "31/03/2026", "Sales Revenue", "5,000.00", "0.00"])         # Duplicate Voucher

    fin_service = FinancialService(test_db)
    preview = fin_service.preview_dataset_import(
        file_path=str(bad_csv),
        dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
        custom_mappings={
            "voucher_number": "Voucher No",
            "date": "Date",
            "account_name": "Account Name",
            "debit": "Debit",
            "credit": "Credit",
        },
    )

    assert preview.validation_passed is False
    assert preview.error_count >= 2
    assert preview.duplicate_count == 1
    err_reasons = [e.error_reason for e in preview.errors]
    assert any("Duplicate" in r for r in err_reasons)
    assert any("Date" in str(e.column_name) or "date" in str(e.column_name) for e in preview.errors)


def test_unbalanced_trial_balance_exact_arithmetic(test_db: DatabaseManager, tmp_path: Path):
    """Test that unbalanced Trial Balance is caught with exact paise discrepancy."""
    unbal_csv = tmp_path / "unbalanced_tb.csv"
    with unbal_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Code", "Account Name", "Opening Dr", "Opening Cr", "Debit", "Credit", "Closing Dr", "Closing Cr"])
        writer.writerow(["1001", "Cash in Hand", "100.00", "0.00", "50.00", "0.00", "150.00", "0.00"])
        writer.writerow(["2001", "Capital Account", "0.00", "100.00", "0.00", "45.00", "0.00", "145.00"])  # 5.00 paise imbalance

    fin_service = FinancialService(test_db)
    preview = fin_service.preview_dataset_import(
        file_path=str(unbal_csv),
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        custom_mappings={
            "account_code": "Account Code",
            "account_name": "Account Name",
            "opening_dr": "Opening Dr",
            "opening_cr": "Opening Cr",
            "debit": "Debit",
            "credit": "Credit",
            "closing_dr": "Closing Dr",
            "closing_cr": "Closing Cr",
        },
    )

    assert preview.is_balanced is False
    assert preview.discrepancy_paise == 500  # 5.00 INR = 500 paise
    assert preview.validation_passed is False
    assert any("out of balance by" in e.error_reason for e in preview.errors)


def test_canonical_mapping_and_lead_schedules(test_db: DatabaseManager, tmp_path: Path):
    """Test mapping: Ledger Account -> Classification -> FS Line -> Audit Area -> Schedule III -> Lead Schedule."""
    tb_csv = tmp_path / "mapping_tb.csv"
    with tb_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Code", "Account Name", "Debit", "Credit", "Closing Dr", "Closing Cr"])
        writer.writerow(["REV-01", "Domestic Product Sales", "0.00", "5,00,000.00", "0.00", "5,00,000.00"])
        writer.writerow(["REC-01", "Sundry Debtors - Domestic", "5,00,000.00", "0.00", "5,00,000.00", "0.00"])

    fin_service = FinancialService(test_db)
    ds = fin_service.import_dataset(
        ImportDatasetDTO(
            engagement_id="eng-fin-101",
            dataset_name="Mapping TB",
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            file_path=str(tb_csv),
            column_mappings={
                "account_code": "Account Code",
                "account_name": "Account Name",
                "debit": "Debit",
                "credit": "Credit",
                "closing_dr": "Closing Dr",
                "closing_cr": "Closing Cr",
            },
        )
    )

    map_service = AccountMappingService(test_db)
    synced = map_service.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id="eng-fin-101", dataset_id=ds.id)
    )
    assert len(synced) == 2

    # Map accounts
    map_service.map_single_account(
        MapAccountDTO(
            engagement_id="eng-fin-101",
            account_code="REV-01",
            schedule_iii_category="Revenue from Operations",
            schedule_iii_line_item="Sale of Products & Services",
            lead_schedule_ref="WP-I1",
            account_type=AccountTypeEnum.INCOME,
            audit_area="Revenue",
        )
    )
    map_service.map_single_account(
        MapAccountDTO(
            engagement_id="eng-fin-101",
            account_code="REC-01",
            schedule_iii_category="Trade Receivables",
            schedule_iii_line_item="Trade Receivables - Undisputed Good",
            lead_schedule_ref="WP-G1",
            account_type=AccountTypeEnum.ASSET,
            audit_area="Trade Receivables",
        )
    )

    # Lead Schedule generation
    adj_service = AuditAdjustmentService(test_db)
    lead_schedules = adj_service.calculate_lead_schedules("eng-fin-101", ds.id)
    assert len(lead_schedules) == 2
    refs = [s.lead_schedule_ref for s in lead_schedules]
    assert "WP-I1" in refs
    assert "WP-G1" in refs


def test_reconciliation_engines_generate_deterministic_exceptions(test_db: DatabaseManager):
    """Test that all reconciliation engines emit deterministic exceptions on discrepancies."""
    fin_service = FinancialService(test_db)

    # 1. BRS Reconciliation (Stale Cheque > 90 days)
    brs_excs = fin_service.run_reconciliation(
        RunReconciliationDTO(
            engagement_id="eng-fin-101",
            reconciliation_type="BRS",
            as_of_date="2026-03-31",
            data={
                "items": [
                    {
                        "bank_account_number": "HDFC-00123",
                        "item_type": "Cheque Issued but Not Presented",
                        "reference_number": "CHQ-9912",
                        "entry_date": "2025-10-15",  # > 90 days old
                        "amount_paise": 45000000,    # ₹4,50,000.00
                    }
                ]
            },
        )
    )
    assert len(brs_excs) == 1
    assert "Stale Cheque" in brs_excs[0].title
    assert brs_excs[0].severity == "Medium"

    # 2. GST 2B Reconciliation (Invoice missing in 2B)
    gst_excs = fin_service.run_reconciliation(
        RunReconciliationDTO(
            engagement_id="eng-fin-101",
            reconciliation_type="GST_2B",
            data={
                "books_invoices": [
                    {
                        "invoice_number": "INV-2026-881",
                        "vendor_gstin": "27AAACB1234F1Z5",
                        "vendor_name": "Bharat Supplies Ltd",
                        "tax_paise": 1800000,
                    }
                ],
                "gstr2b_invoices": [],  # Missing in 2B
            },
        )
    )
    assert len(gst_excs) == 1
    assert "Missing in GSTR-2B" in gst_excs[0].title

    # 3. Fixed Asset Anomaly (Over-depreciation negative NBV)
    fa_excs = fin_service.run_reconciliation(
        RunReconciliationDTO(
            engagement_id="eng-fin-101",
            reconciliation_type="FIXED_ASSETS",
            as_of_date="2026-03-31",
            data={
                "assets": [
                    {
                        "asset_tag": "FA-GEN-01",
                        "asset_name": "Heavy Diesel Generator",
                        "gross_block_paise": 100000000,
                        "accumulated_depreciation_paise": 105000000,  # Acc Dep > Gross
                        "is_physically_verified": True,
                        "title_deeds_in_company_name": True,
                    }
                ]
            },
        )
    )
    assert len(fa_excs) == 1
    assert "Negative Net Book Value" in fa_excs[0].title


def test_create_audit_work_from_analytics_no_dead_ends(test_db: DatabaseManager, tmp_path: Path):
    """Test that an analytics anomaly creates complete, bidirectional audit work with zero dead ends."""
    gl_csv = tmp_path / "analytics_gl.csv"
    with gl_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Voucher No", "Date", "Account Name", "Debit", "Credit", "Narration"])
        # Duplicate round-number transactions on Sunday
        writer.writerow(["V-101", "29/03/2026", "Consulting Fees", "5,00,000.00", "0.00", "Management fee"])
        writer.writerow(["V-102", "29/03/2026", "Consulting Fees", "5,00,000.00", "0.00", "Management fee"])

    fin_service = FinancialService(test_db)
    ds = fin_service.import_dataset(
        ImportDatasetDTO(
            engagement_id="eng-fin-101",
            dataset_name="GL for Analytics",
            dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
            file_path=str(gl_csv),
            column_mappings={
                "voucher_number": "Voucher No",
                "date": "Date",
                "account_name": "Account Name",
                "debit": "Debit",
                "credit": "Credit",
                "narration": "Narration",
            },
        )
    )

    # Run analytics
    exceptions = fin_service.run_deterministic_analytics(ds.id)
    assert len(exceptions) > 0

    target_exc = exceptions[0]

    # Auditor clicks "CREATE AUDIT WORK"
    audit_work = fin_service.create_audit_work(
        CreateAuditWorkDTO(
            engagement_id="eng-fin-101",
            dataset_id=ds.id,
            source="Deterministic Analytics Engine",
            rule_or_analytic_id=target_exc.analytic_id,
            title=target_exc.title,
            description=target_exc.description,
            severity="High",
            audit_area="Expenses",
            assertion="Occurrence and Measurement",
            objective="Substantively test duplicate round number expense entries.",
            implicated_rows=target_exc.implicated_rows or [2, 3],
            computed_evidence=target_exc.computed_evidence,
            preparer="Senior Auditor",
        )
    )

    proc = audit_work["procedure"]
    wp = audit_work["working_paper"]
    finding = audit_work["finding"]
    test_exec = audit_work["test_execution"]
    evidence = audit_work["evidence"]

    # Verify procedure attributes
    assert proc.engagement_id == "eng-fin-101"
    assert proc.audit_area == "Expenses"
    assert proc.assertion == AssertionEnum.OCCURRENCE
    assert proc.population != ""
    assert proc.methodology == target_exc.analytic_id


    # Verify test execution attributes
    assert test_exec.procedure_id == proc.id
    assert test_exec.result == "EXCEPTION_IDENTIFIED"
    assert len(test_exec.exceptions) == 1

    # Verify finding & working paper linkage
    assert finding.working_paper_id == wp.id
    assert evidence.id in finding.evidence_ids

    # Verify bidirectional navigation in graph
    trace_service = TraceabilityService(test_db)
    ev_findings = trace_service.get_findings_for_evidence("eng-fin-101", evidence.id)
    assert any(f.id == finding.id for f in ev_findings)

    wp_procs = trace_service.get_procedures_for_working_paper("eng-fin-101", wp.id)
    assert any(p.id == proc.id for p in wp_procs)


def test_large_dataset_performance_and_exact_balance(test_db: DatabaseManager, tmp_path: Path):
    """Test importing and validating 10,000 rows with exact integer paise calculations."""
    large_csv = tmp_path / "large_tb.csv"
    with large_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Code", "Account Name", "Opening Dr", "Opening Cr", "Debit", "Credit", "Closing Dr", "Closing Cr"])
        for i in range(1, 5001):
            writer.writerow([f"DR-{i}", f"Debtor Account {i}", "0.00", "0.00", "1,234.50", "0.00", "1,234.50", "0.00"])
            writer.writerow([f"CR-{i}", f"Creditor Account {i}", "0.00", "0.00", "0.00", "1,234.50", "0.00", "1,234.50"])

    fin_service = FinancialService(test_db)
    preview = fin_service.preview_dataset_import(
        file_path=str(large_csv),
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        custom_mappings={
            "account_code": "Account Code",
            "account_name": "Account Name",
            "opening_dr": "Opening Dr",
            "opening_cr": "Opening Cr",
            "debit": "Debit",
            "credit": "Credit",
            "closing_dr": "Closing Dr",
            "closing_cr": "Closing Cr",
        },
    )

    assert preview.total_rows == 10000
    assert preview.valid_rows_count == 10000
    assert preview.error_count == 0
    assert preview.is_balanced is True
    # 5000 * 1234.50 = 6,172,500.00 INR = 617,250,000 paise
    assert preview.total_debit_paise == 617250000
    assert preview.total_credit_paise == 617250000
