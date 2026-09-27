"""Regression tests verifying determinism, provenance, and quad-actions across all financial analytics engines."""

import uuid
from datetime import date
from decimal import Decimal

import pytest

from finauditpro.application.financial_dtos import CreateAuditWorkDTO, RunReconciliationDTO
from finauditpro.application.services.financial_service import FinancialService
from finauditpro.domain.audit_matrix_entities import AssertionEnum, BenchmarkTypeEnum
from finauditpro.domain.bank_reconciliation_engine import (
    BankReconciliationEngine,
    BRSExceptionSeverityEnum,
    BRSItemTypeEnum,
)
from finauditpro.domain.cash_flow_evaluation_engine import (
    build_indirect_cash_flow_statement,
    build_statement_of_changes_in_equity,
)
from finauditpro.domain.continuous_reconciliation_engine import ContinuousReconciliationEngine
from finauditpro.domain.cutoff_testing_engine import (
    CutOffExceptionTypeEnum,
    CutOffTestingEngine,
)
from finauditpro.domain.deferred_tax_engine import (
    DeferredTaxEngine,
    TimingDifferenceTypeEnum,
)
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.domain.financial_entities import (
    BankTransaction,
    DatasetStatusEnum,
    DatasetTypeEnum,
    FinancialDataset,
    LedgerEntry,
    TrialBalanceLine,
)
from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    BalanceSheetLineItem,
    ProfitAndLossLineItem,
    ProfitAndLossStatement,
)
from finauditpro.domain.fixed_asset_engine import AssetAnomalyTypeEnum, FixedAssetEngine
from finauditpro.domain.going_concern_engine import (
    GoingConcernEngine,
    SolvencyRiskLevelEnum,
)
from finauditpro.domain.gst_reconciliation_engine import (
    GSTReconciliationEngine,
    MatchStatusEnum,
)
from finauditpro.domain.inventory_count_engine import (
    InventoryCountEngine,
    InventoryDiscrepancyTypeEnum,
)
from finauditpro.domain.journal_analytics_engine import JournalAnalyticsEngine
from finauditpro.domain.materiality_engine import MaterialityEngine
from finauditpro.domain.pattern_detection_engine import PatternDetectionEngine
from finauditpro.domain.payroll_forensic_engine import (
    PayrollAnomalyTypeEnum,
    PayrollForensicEngine,
)
from finauditpro.domain.receivables_recovery_engine import (
    ReceivablesRecoveryEngine,
    RecoveryStatusEnum,
)
from finauditpro.domain.related_party_engine import (
    RelatedPartyCategoryEnum,
    RelatedPartyEngine,
    RelatedPartyEntity,
)
from finauditpro.domain.sampling_engine import AuditSamplingEngine
from finauditpro.domain.three_way_match_engine import (
    MatchDiscrepancyTypeEnum,
    ThreeWayMatchEngine,
)
from finauditpro.domain.value_objects import Money
from finauditpro.infrastructure.analytics.analytics_engine import DeterministicAnalyticsEngine
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
)


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_analytics_audit.db"
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def seeded_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(name="Test Audit Firm LLP"))
        client = ClientRepository(session).add(
            Client(firm_id=firm.id, name="Apex Enterprises Ltd", pan="AABCA1234F")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-2026",
                title="Statutory Audit FY 2025-26",
            )
        )
        return eng


class TestFinancialAnalyticsEnginesAudit:
    """Comprehensive regression tests for all financial analytics engines."""

    def test_materiality_engine_determinism_and_precision(self):
        """Materiality calculations must be 100% deterministic with exact paise precision."""
        res1 = MaterialityEngine.calculate(
            engagement_id="eng-1",
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount_paise=100_00_00_000_00,  # 100 Crores INR
            overall_percentage=1.0,
            performance_percentage=75.0,
            trivial_percentage=5.0,
        )
        res2 = MaterialityEngine.calculate(
            engagement_id="eng-1",
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount_paise=100_00_00_000_00,
            overall_percentage=1.0,
            performance_percentage=75.0,
            trivial_percentage=5.0,
        )

        assert res1.overall_materiality_paise == 1_00_00_000_00  # 1 Crore INR = 1%
        assert res1.performance_materiality_paise == 75_00_000_00  # 75 Lakhs INR = 75% of 1 Cr
        assert res1.clearly_trivial_threshold_paise == 5_00_000_00  # 5 Lakhs INR = 5% of 1 Cr

        # Invariant: Bit-for-bit identical outputs
        assert res1.overall_materiality_paise == res2.overall_materiality_paise
        assert res1.performance_materiality_paise == res2.performance_materiality_paise
        assert res1.clearly_trivial_threshold_paise == res2.clearly_trivial_threshold_paise

        # Monetary classification verification
        assert MaterialityEngine.classify_monetary_amount(4_00_000_00, res1) == "Clearly Trivial"
        assert MaterialityEngine.classify_monetary_amount(80_00_000_00, res1) == "Above Performance Materiality"
        assert MaterialityEngine.classify_monetary_amount(1_50_00_000_00, res1) == "Above Overall Materiality"

    def test_benford_law_determinism_and_chi_square(self):
        """Benford's Law distribution analysis must compute identical Chi-Square values."""
        # Synthesize 100 amounts strictly conforming to natural logarithmic distribution
        engine = JournalAnalyticsEngine()
        natural_amounts = []
        for d in range(1, 10):
            count = int(100 * (10 - d) / 5)
            natural_amounts.extend([d * 100000 + i * 100 for i in range(count)])

        res1 = engine.analyze_benford_distribution(natural_amounts)
        res2 = engine.analyze_benford_distribution(natural_amounts)

        assert res1.eligible_count == res2.eligible_count
        assert res1.chi_square_stat == res2.chi_square_stat
        assert res1.deviation_detected == res2.deviation_detected

        # Synthesize heavily biased amounts starting with '9'
        biased_amounts = [9999900 + i for i in range(80)]
        res_biased = engine.analyze_benford_distribution(biased_amounts)
        assert res_biased.deviation_detected is True
        assert res_biased.chi_square_stat > 15.507

    def test_duplicate_and_outlier_detection_determinism(self):
        """Duplicate detection and Z-Score outlier analysis must be deterministic."""
        entries = [
            LedgerEntry(
                dataset_id="ds-1",
                source_row_no=1,
                entry_date="2026-03-15",
                voucher_number="VCH-101",
                account_name="Vendor A",
                debit_paise=5000000,
                credit_paise=0,
            ),
            LedgerEntry(
                dataset_id="ds-1",
                source_row_no=2,
                entry_date="2026-03-15",
                voucher_number="VCH-102",
                account_name="Vendor A",
                debit_paise=5000000,
                credit_paise=0,
            ),
            LedgerEntry(
                dataset_id="ds-1",
                source_row_no=3,
                entry_date="2026-03-16",
                voucher_number="VCH-103",
                account_name="Vendor B",
                debit_paise=100000000,  # 10 Lakhs (Outlier)
                credit_paise=0,
            ),
            LedgerEntry(
                dataset_id="ds-1",
                source_row_no=4,
                entry_date="2026-03-17",
                voucher_number="VCH-104",
                account_name="Vendor C",
                debit_paise=100000,
                credit_paise=0,
            ),
            LedgerEntry(
                dataset_id="ds-1",
                source_row_no=5,
                entry_date="2026-03-18",
                voucher_number="VCH-105",
                account_name="Vendor D",
                debit_paise=120000,
                credit_paise=0,
            ),
            LedgerEntry(
                dataset_id="ds-1",
                source_row_no=6,
                entry_date="2026-03-19",
                voucher_number="VCH-106",
                account_name="Vendor E",
                debit_paise=110000,
                credit_paise=0,
            ),
        ]

        dupes1 = DeterministicAnalyticsEngine.detect_duplicates("ds-1", entries)
        dupes2 = DeterministicAnalyticsEngine.detect_duplicates("ds-1", entries)
        assert len(dupes1.exceptions) == len(dupes2.exceptions) == 1
        assert dupes1.exceptions[0].implicated_rows == [1, 2]

        outliers1 = DeterministicAnalyticsEngine.detect_large_amount_outliers("ds-1", entries, z_threshold=2.0)
        outliers2 = DeterministicAnalyticsEngine.detect_large_amount_outliers("ds-1", entries, z_threshold=2.0)
        assert len(outliers1.exceptions) == len(outliers2.exceptions) == 1
        assert outliers1.exceptions[0].implicated_rows == [3]

    def test_cutoff_testing_engine_invariants(self):
        """Cut-off testing must accurately identify pre-close unbilled and post-close return anomalies."""
        txns = [
            {
                "document_number": "INV-101",
                "document_date": "2026-03-25",
                "dispatch_or_receipt_date": "2026-03-25",
                "counterparty_name": "Client A",
                "amount_paise": 10000000,
                "transaction_type": "Sales",
            },
            {
                "document_number": "RET-201",
                "document_date": "2026-04-05",  # 5 days post year-end
                "dispatch_or_receipt_date": "2026-04-05",
                "counterparty_name": "Client B",
                "amount_paise": 50000000,  # 5 Lakhs
                "transaction_type": "Returns",
            },
            {
                "document_number": "INV-301",
                "document_date": "2026-04-02",  # Billed in April
                "dispatch_or_receipt_date": "2026-03-28",  # Dispatched in March
                "counterparty_name": "Client C",
                "amount_paise": 25000000,
                "transaction_type": "Sales",
            },
        ]

        sum1 = CutOffTestingEngine.analyze_cutoff_records("eng-1", "2026-03-31", txns)
        sum2 = CutOffTestingEngine.analyze_cutoff_records("eng-1", "2026-03-31", txns)

        assert sum1.total_inspected_items == 3
        assert sum1.clean_items_count == 1
        assert sum1.exception_count == 2
        assert sum1.total_exception_value_paise == 75000000
        assert sum1.total_exception_value_paise == sum2.total_exception_value_paise

        exc_types = [r.exception_type for r in sum1.records]
        assert CutOffExceptionTypeEnum.POST_YEAR_END_SALES_RETURN in exc_types
        assert CutOffExceptionTypeEnum.PRE_YEAR_END_UNBILLED_DISPATCH in exc_types

    def test_bank_reconciliation_engine_stale_and_delay_rules(self):
        """BRS engine must identify >90 day stale cheques and >15 day delayed deposits."""
        items = [
            {
                "bank_account_number": "HDFC-001",
                "item_type": BRSItemTypeEnum.UNPRESENTED_CHEQUE,
                "reference_number": "CHQ-1001",
                "entry_date": "2025-11-15",  # > 90 days as of 2026-03-31
                "amount_paise": 20000000,
            },
            {
                "bank_account_number": "HDFC-001",
                "item_type": BRSItemTypeEnum.UNCREDITED_DEPOSIT,
                "reference_number": "DEP-2001",
                "entry_date": "2026-03-10",  # 21 days pending (> 15 days)
                "amount_paise": 30000000,
            },
            {
                "bank_account_number": "HDFC-001",
                "item_type": BRSItemTypeEnum.UNPRESENTED_CHEQUE,
                "reference_number": "CHQ-3001",
                "entry_date": "2026-03-25",  # Normal timing difference (6 days)
                "amount_paise": 5000000,
            },
        ]

        brs1 = BankReconciliationEngine.audit_brs_statement("eng-1", "2026-03-31", items)
        brs2 = BankReconciliationEngine.audit_brs_statement("eng-1", "2026-03-31", items)

        assert brs1.stale_cheques_count == 1
        assert brs1.delayed_deposits_count == 1
        assert brs1.at_risk_amount_paise == 50000000
        assert brs1.at_risk_amount_paise == brs2.at_risk_amount_paise

    def test_gst_2b_reconciliation_engine_matching_invariants(self):
        """GST 2B engine must verify 3-way match, missing 2B entries, and Sec 17(5) blocked ITC."""
        books = [
            {
                "invoice_number": "INV-A1",
                "vendor_gstin": "27AAACA1234F1Z1",
                "vendor_name": "Supplier A",
                "taxable_paise": 10000000,
                "tax_paise": 1800000,
            },
            {
                "invoice_number": "INV-B2",
                "vendor_gstin": "27AAACB5678F1Z2",
                "vendor_name": "Supplier B",
                "taxable_paise": 20000000,
                "tax_paise": 3600000,
            },
            {
                "invoice_number": "INV-C3",
                "vendor_gstin": "27AAACC9999F1Z3",
                "vendor_name": "Supplier C",
                "taxable_paise": 5000000,
                "tax_paise": 900000,
                "is_sec_17_5_blocked": True,
            },
        ]
        gstr2b = [
            {
                "invoice_number": "INV-A1",
                "vendor_gstin": "27AAACA1234F1Z1",
                "taxable_paise": 10000000,
                "tax_paise": 1800000,  # Exact match
            },
            # INV-B2 is missing in 2B (Vendor non-filing)
            {
                "invoice_number": "INV-C3",
                "vendor_gstin": "27AAACC9999F1Z3",
                "taxable_paise": 5000000,
                "tax_paise": 900000,
            },
        ]

        gst_sum = GSTReconciliationEngine.match_purchase_register_with_2b("eng-1", books, gstr2b)

        assert gst_sum.matched_count == 1
        assert gst_sum.mismatched_count == 1  # Missing in 2B
        assert gst_sum.ineligible_count == 1  # Sec 17(5)
        assert gst_sum.eligible_2b_itc_paise == 1800000
        assert gst_sum.at_risk_itc_paise == 4500000  # 3600000 (missing) + 900000 (blocked)

    def test_three_way_match_po_grn_invoice(self):
        """Three-way match engine must detect quantity, rate, and missing documentation discrepancies."""
        orders = [
            {
                "po_number": "PO-1",
                "grn_number": "GRN-1",
                "invoice_number": "INV-1",
                "vendor_name": "Vendor 1",
                "item_description": "Steel",
                "po_quantity": 100.0,
                "grn_quantity": 100.0,
                "invoice_quantity": 100.0,
                "po_rate_paise": 5000,
                "invoice_rate_paise": 5000,
                "invoice_total_paise": 500000,
            },
            {
                "po_number": "PO-2",
                "grn_number": "GRN-2",
                "invoice_number": "INV-2",
                "vendor_name": "Vendor 2",
                "item_description": "Cement",
                "po_quantity": 50.0,
                "grn_quantity": 40.0,  # Received 40, Billed 50
                "invoice_quantity": 50.0,
                "po_rate_paise": 3000,
                "invoice_rate_paise": 3000,
                "invoice_total_paise": 150000,
            },
        ]

        match_sum = ThreeWayMatchEngine.match_orders("eng-1", orders)
        assert match_sum.fully_matched_count == 1
        assert match_sum.discrepancy_count == 1
        assert match_sum.records[1].discrepancy_type == MatchDiscrepancyTypeEnum.QUANTITY_VARIANCE
        assert match_sum.records[1].discrepancy_amount_paise == 30000  # 10 * 3000

    def test_fixed_asset_engine_caro_verification(self):
        """Fixed asset engine must detect negative NBV, unlocated ghost assets, and stagnant CWIP."""
        assets = [
            {
                "asset_tag": "FA-001",
                "asset_name": "Lathe Machine",
                "gross_block_paise": 50000000,
                "accumulated_depreciation_paise": 60000000,  # Negative NBV!
                "location": "Plant 1",
            },
            {
                "asset_tag": "FA-002",
                "asset_name": "Delivery Van",
                "gross_block_paise": 80000000,
                "accumulated_depreciation_paise": 20000000,
                "is_physically_verified": False,  # Ghost Asset
            },
            {
                "asset_tag": "FA-003",
                "asset_name": "Factory Building Expansion (CWIP)",
                "gross_block_paise": 200000000,
                "accumulated_depreciation_paise": 0,
                "cwip_age_months": 36,  # Stagnant > 2 years
            },
        ]

        fa_sum = FixedAssetEngine.audit_fixed_asset_register("eng-1", assets)
        assert fa_sum.total_assets_inspected == 3
        assert fa_sum.anomalous_assets_count == 3
        types = [r.anomaly_type for r in fa_sum.records]
        assert AssetAnomalyTypeEnum.NEGATIVE_NET_BOOK_VALUE in types
        assert AssetAnomalyTypeEnum.GHOST_ASSET_UNLOCATED in types
        assert AssetAnomalyTypeEnum.CWIP_AGEING_STAGNANT in types

    def test_receivables_recovery_engine_subsequent_tie_out(self):
        """Receivables recovery engine must match post-balance sheet collections and calculate ECL provisions."""
        debtors = [
            {"debtor_code": "D-101", "debtor_name": "Customer Alpha", "balance_at_year_end_paise": 10000000},
            {"debtor_code": "D-102", "debtor_name": "Customer Beta", "balance_at_year_end_paise": 20000000},
            {"debtor_code": "D-103", "debtor_name": "Customer Gamma", "balance_at_year_end_paise": 30000000},
        ]
        receipts = [
            {"debtor_code": "D-101", "receipt_amount_paise": 10000000},  # 100% recovered
            {"debtor_code": "D-102", "receipt_amount_paise": 10000000},  # 50% recovered
            # D-103 has 0 receipts
        ]

        rec_sum = ReceivablesRecoveryEngine.tie_out_subsequent_receipts("eng-1", debtors, receipts)
        assert rec_sum.fully_recovered_count == 1
        assert rec_sum.partially_recovered_count == 1
        assert rec_sum.unrecovered_count == 1
        assert rec_sum.records[0].recovery_status == RecoveryStatusEnum.FULLY_RECOVERED
        assert rec_sum.records[1].recovery_status == RecoveryStatusEnum.PARTIALLY_RECOVERED
        assert rec_sum.records[2].recovery_status == RecoveryStatusEnum.UNRECOVERED_OVERDUE
        assert rec_sum.records[2].ecl_provision_recommended_paise == 30000000

    def test_related_party_and_section_188_engine(self):
        """Related-party engine must detect undeclared KMP transactions and Section 188 non-compliance."""
        declared = [
            RelatedPartyEntity(
                engagement_id="eng-1",
                party_name="Director Sister Entity",
                relationship_category=RelatedPartyCategoryEnum.COMMON_DIRECTORSHIP_ENTITY,
                pan_or_din="AAACD1234K",
            )
        ]
        transactions = [
            {
                "account_name": "Director Sister Entity",
                "pan": "AAACD1234K",
                "amount_paise": 50000000,
                "is_at_arms_length": True,
                "has_audit_committee_approval": True,
            },
            {
                "account_name": "Undeclared Consultant Enterprise",
                "pan": "ABCDE9999K",  # Matches Managing Director's PAN!
                "amount_paise": 25000000,
                "is_at_arms_length": False,
                "has_audit_committee_approval": False,
            },
        ]
        kmp_pans = ["ABCDE9999K", "XYZAB1111P"]

        rp_res = RelatedPartyEngine.scan_ledger_against_kmp_master(declared, transactions, kmp_pans)
        assert len(rp_res.undeclared_vendor_matches) == 1
        assert rp_res.undeclared_vendor_matches[0]["pan"] == "ABCDE9999K"
        assert rp_res.unapproved_count == 1
        assert rp_res.non_arms_length_count == 1

    def test_payroll_forensic_and_ghost_employee_engine(self):
        """Payroll engine must flag duplicate bank accounts, duplicate PANs, and disbursements to inactive staff."""
        entries = [
            {
                "employee_code": "EMP-001",
                "employee_name": "Alice Smith",
                "pan": "ABCDE1234F",
                "bank_account_number": "ACC-9999",
                "salary_paise": 10000000,
                "is_active": True,
            },
            {
                "employee_code": "EMP-002",
                "employee_name": "Ghost John",
                "pan": "ABCDE5678F",
                "bank_account_number": "ACC-9999",  # DUPLICATE BANK ACCOUNT!
                "salary_paise": 10000000,
                "is_active": True,
            },
            {
                "employee_code": "EMP-003",
                "employee_name": "Resigned Bob",
                "pan": "ABCDE7777F",
                "bank_account_number": "ACC-1234",
                "salary_paise": 15000000,
                "is_active": False,  # Resigned
                "resignation_date": "2025-12-31",
            },
            {
                "employee_code": "EMP-004",
                "employee_name": "Clean Worker",
                "pan": "ABCDE8888F",
                "bank_account_number": "ACC-5555",
                "salary_paise": 8000000,
                "is_active": True,
            },
        ]

        pay_sum = PayrollForensicEngine.scan_payroll_master("eng-1", entries)
        assert pay_sum.clean_entries_count == 1
        assert pay_sum.ghost_employee_anomalies_count == 3
        anom_types = [r.anomaly_type for r in pay_sum.records]
        assert PayrollAnomalyTypeEnum.DUPLICATE_BANK_ACCOUNT in anom_types
        assert PayrollAnomalyTypeEnum.PAYMENT_TO_INACTIVE_EMPLOYEE in anom_types

    def test_audit_sampling_engine_mus_and_reproducibility(self):
        """Monetary Unit Sampling must calculate consistent sampling intervals and high-value stratification."""
        pop = [
            {"voucher_no": f"V-{i}", "amount_paise": (i + 1) * 1000000}
            for i in range(20)
        ]
        # Total pop = (1 + ... + 20) * 10,000 INR = 2,100,000 INR = 210,000,000 paise

        mus1 = AuditSamplingEngine.calculate_mus_sample(
            population_records=pop,
            tolerable_misstatement_paise=30000000,
            confidence_level_pct=95.0,
        )
        mus2 = AuditSamplingEngine.calculate_mus_sample(
            population_records=pop,
            tolerable_misstatement_paise=30000000,
            confidence_level_pct=95.0,
        )

        assert mus1.sampling_interval_paise == mus2.sampling_interval_paise
        assert mus1.sample_size == mus2.sample_size
        assert len(mus1.high_value_items) == len(mus2.high_value_items)

        # Reproducible random sampling with seed
        rnd1 = AuditSamplingEngine.calculate_random_sample(pop, sample_size=5, random_seed=12345)
        rnd2 = AuditSamplingEngine.calculate_random_sample(pop, sample_size=5, random_seed=12345)
        assert [i["voucher_no"] for i in rnd1.selected_items] == [i["voucher_no"] for i in rnd2.selected_items]

    def test_deferred_tax_engine_as22_computation(self):
        """Deferred tax engine must compute exact DTA/DTL schedule based on timing differences."""
        items = [
            {
                "item_name": "Property, Plant & Equipment Depreciation",
                "difference_type": TimingDifferenceTypeEnum.DEPRECIATION_DIFFERENCE,
                "books_carrying_paise": 100000000,
                "tax_base_paise": 80000000,  # Books > Tax -> Future Taxable -> DTL
            },
            {
                "item_name": "Section 43B Bonus Disallowance",
                "difference_type": TimingDifferenceTypeEnum.SECTION_43B_DISALLOWANCE,
                "books_carrying_paise": 0,
                "tax_base_paise": 10000000,  # Disallowed -> Future Deductible -> DTA
            },
        ]

        dt_sum = DeferredTaxEngine.calculate_deferred_tax("eng-1", tax_rate_pct=25.0, timing_items=items)
        assert dt_sum.total_taxable_differences_paise == 20000000
        assert dt_sum.total_deductible_differences_paise == 10000000
        assert dt_sum.net_deferred_tax_liability_paise == 2500000  # (20M - 10M) * 25% = 2.5M paise

    def test_going_concern_engine_solvency_evaluation(self):
        """Going concern engine must determine critical risk and SA 570 disclosure requirements."""
        res_crit, unc_crit, _ = GoingConcernEngine.evaluate_indicators(
            has_operating_losses=True,
            has_negative_operating_cashflow=True,
            has_negative_net_worth=True,  # Negative Net Worth trigger
            has_covenant_breaches=False,
            has_debt_maturity_unfunded=False,
        )
        assert res_crit == SolvencyRiskLevelEnum.CRITICAL_GOING_CONCERN_RISK
        assert unc_crit is True

        res_low, unc_low, _ = GoingConcernEngine.evaluate_indicators(
            has_operating_losses=False,
            has_negative_operating_cashflow=False,
            has_negative_net_worth=False,
            has_covenant_breaches=False,
            has_debt_maturity_unfunded=False,
        )
        assert res_low == SolvencyRiskLevelEnum.LOW
        assert unc_low is False

    def test_quad_action_pipeline_create_audit_work(self, db_manager, seeded_engagement):
        """Quad-action pipeline must convert analytical exceptions into Risk, Procedure, Evidence, Finding, and Working Paper."""
        fin_service = FinancialService(db_manager)

        # 1. Ingest dataset
        with db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            ds = repo.add_dataset(
                FinancialDataset(
                    id=str(uuid.uuid4()),
                    engagement_id=seeded_engagement.id,
                    dataset_name="General Ledger FY26",
                    dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
                    status=DatasetStatusEnum.IMPORTED,
                )
            )

        # 2. Run create_audit_work (Quad Action: EXCEPTION, INVESTIGATE, CREATE PROCEDURE, CREATE WORKING PAPER)
        dto = CreateAuditWorkDTO(
            engagement_id=seeded_engagement.id,
            dataset_id=ds.id,
            rule_or_analytic_id="SA-315-CUTOFF-ENGINE",
            audit_area="Revenue",
            title="Revenue Cut-off Exception: Post Year-End Return",
            description="High value sales return of ₹5,00,000 booked 5 days post year-end.",
            severity="High",
            assertion="Cut-off",
            implicated_rows=[102, 105],
            computed_evidence="Voucher RET-201 dated 2026-04-05",
            objective="Verify that revenue returns are accounted for in correct accounting period.",
            source="CutOffTestingEngine v1.0.0",
            preparer="Lead Senior Auditor",
        )

        audit_work = fin_service.create_audit_work(dto)

        assert audit_work["risk"] is not None
        assert audit_work["risk"].category == "Revenue"
        assert audit_work["procedure"] is not None
        assert audit_work["procedure"].assertion == AssertionEnum.CUT_OFF
        assert audit_work["working_paper"] is not None
        assert audit_work["finding"] is not None
        assert audit_work["evidence"] is not None
        assert audit_work["test_execution"] is not None
        assert audit_work["test_execution"].result == "EXCEPTION_IDENTIFIED"
        assert len(audit_work["test_execution"].exceptions) == 1
        assert audit_work["test_execution"].exceptions[0].severity == "High"
