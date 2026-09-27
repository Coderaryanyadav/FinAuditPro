"""Unit tests verifying newly added CA Workstation capabilities."""

import pytest
from finauditpro.domain.entities import Firm, Client, Engagement, AuditTypeEnum, EngagementStatusEnum
from finauditpro.domain.financial_entities import FinancialDataset, FinancialRecord
from finauditpro.domain.audit_matrix_entities import BenchmarkTypeEnum
from finauditpro.domain.sampling_engine import AuditSamplingEngine
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    FirmRepository,
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
)


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_ca_workstation.db"
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def seeded_engagement_with_tb(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(name="Apex & Co Chartered Accountants"))
        client = ClientRepository(session).add(
            Client(firm_id=firm.id, name="Bharati Global Manufacturing Ltd", pan="AABCB9999F")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-2026",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            )
        )
        # Add imported Trial Balance dataset
        fin_repo = FinancialDataRepository(session)
        ds = fin_repo.add_dataset(
            FinancialDataset(
                engagement_id=eng.id,
                dataset_name="FY 2025-26 Closing Trial Balance",
                period_name="FY 2025-2026",
            )
        )
        fin_repo.add_records([
            FinancialRecord(
                dataset_id=ds.id,
                row_index=1,
                account_code="4001",
                account_name="Domestic Product Sales Revenue",
                debit=0.0,
                credit=50000000.0,  # 5 Crore INR Revenue
            ),
            FinancialRecord(
                dataset_id=ds.id,
                row_index=2,
                account_code="5001",
                account_name="Raw Material Cost & Expenses",
                debit=40000000.0,  # 4 Crore INR Expense
                credit=0.0,
            ),
            FinancialRecord(
                dataset_id=ds.id,
                row_index=3,
                account_code="1001",
                account_name="Plant & Machinery Fixed Assets",
                debit=25000000.0,  # 2.5 Crore INR Asset
                credit=0.0,
            ),
            FinancialRecord(
                dataset_id=ds.id,
                row_index=4,
                account_code="3001",
                account_name="Share Capital & Equity Reserves",
                debit=0.0,
                credit=15000000.0,  # 1.5 Crore INR Equity
                credit_paise=1500000000,
            ),
        ])
        return eng


class TestCAWorkstationFeatures:
    """Test suite covering high-value CA workstation enhancements."""

    def test_auto_derive_materiality_benchmarks_from_tb(self, db_manager, seeded_engagement_with_tb):
        """Materiality benchmark should be automatically derived from imported trial balance."""
        mat_service = MaterialityService(db_manager)

        # 1. Revenue benchmark
        rev_paise = mat_service.auto_derive_benchmark_from_trial_balance(
            seeded_engagement_with_tb.id, BenchmarkTypeEnum.REVENUE
        )
        assert rev_paise == 5000000000  # ₹50,00,000.00 * 100

        # 2. Profit Before Tax benchmark (5 Cr Revenue - 4 Cr Expense = 1 Cr PBT)
        pbt_paise = mat_service.auto_derive_benchmark_from_trial_balance(
            seeded_engagement_with_tb.id, BenchmarkTypeEnum.PROFIT_BEFORE_TAX
        )
        assert pbt_paise == 1000000000  # ₹1,00,00,000.00 * 100

        # 3. Total Assets benchmark
        asset_paise = mat_service.auto_derive_benchmark_from_trial_balance(
            seeded_engagement_with_tb.id, BenchmarkTypeEnum.TOTAL_ASSETS
        )
        assert asset_paise == 2500000000  # ₹25,00,000.00 * 100

        # 4. Equity benchmark
        eq_paise = mat_service.auto_derive_benchmark_from_trial_balance(
            seeded_engagement_with_tb.id, BenchmarkTypeEnum.EQUITY
        )
        assert eq_paise == 1500000000  # ₹15,00,000.00 * 100

    def test_statistical_mus_sampling_engine(self):
        """SA 530 Monetary Unit Sampling should isolate high-value items and calculate sampling intervals."""
        vouchers = [
            {"voucher_no": "V-001", "account": "Purchases", "amount": 500000.0},
            {"voucher_no": "V-002", "account": "Purchases", "amount": 25000.0},
            {"voucher_no": "V-003", "account": "Purchases", "amount": 1200000.0},  # High Value
            {"voucher_no": "V-004", "account": "Purchases", "amount": 45000.0},
            {"voucher_no": "V-005", "account": "Purchases", "amount": 800000.0},
        ]
        # Tolerable misstatement = ₹10,00,000 (100000000 paise), 95% confidence factor = 3.0 -> Interval ≈ ₹3,33,333
        result = AuditSamplingEngine.calculate_mus_sample(
            population_records=vouchers,
            tolerable_misstatement_paise=100000000,
            confidence_level_pct=95.0,
        )

        assert result.sample_size >= 2
        assert len(result.high_value_items) >= 2  # V-001 and V-003 exceed the sampling interval
        assert result.total_sampled_value_paise > 0
