"""Tests for Adjusted Trial Balance, Schedule III Lead Schedules, Invariants, and Scalability."""

import time

import pytest

from finauditpro.application.account_mapping_dtos import (
    MapAccountDTO,
    SyncTrialBalanceAccountsDTO,
    ValidateMappingsDTO,
)
from finauditpro.application.audit_adjustment_dtos import (
    CreateAJEDTO,
    CreateAJELineDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
)
from finauditpro.domain.financial_entities import (
    DatasetTypeEnum,
    FinancialDataset,
    TrialBalanceLine,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture(autouse=True)
def clean_security_context():
    SecurityContext.clear()
    yield
    SecurityContext.clear()


@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_adj_tb.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_environment(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-1", name="CA Audit Firm"))
        user_repo = UserRepository(session)
        user_repo.add(
            User(id="user-assoc", username="assoc1", password_hash="h", salt="s", role="Associate")
        )
        user_repo.add(
            User(id="user-mgr", username="mgr1", password_hash="h", salt="s", role="Manager")
        )
        client = ClientRepository(session).add(
            Client(id="client-1", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                id="eng-1",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        return eng


def test_complete_phase_a_acceptance_workflow(db_manager, seed_environment):
    """End-to-end acceptance test covering the entire Phase A workflow."""
    eng = seed_environment
    map_service = AccountMappingService(db_manager)
    adj_service = AuditAdjustmentService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="user-assoc", username="assoc1", role=RoleEnum.ASSOCIATE)
    )

    # Step 1: Import Trial Balance with Balanced Figures
    # Assets = ₹1,00,00,000, Liabilities = ₹1,00,00,000
    dataset = FinancialDataset(
        id="ds-e2e",
        engagement_id=eng.id,
        dataset_name="E2E_TB.xlsx",
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
    )
    tb_lines = [
        TrialBalanceLine(
            dataset_id="ds-e2e",
            source_row_no=1,
            account_code="1010",
            account_name="Factory Building",
            closing_dr_paise=50000000,
        ),
        TrialBalanceLine(
            dataset_id="ds-e2e",
            source_row_no=2,
            account_code="1020",
            account_name="Trade Debtors",
            closing_dr_paise=30000000,
        ),
        TrialBalanceLine(
            dataset_id="ds-e2e",
            source_row_no=3,
            account_code="1030",
            account_name="HDFC Bank",
            closing_dr_paise=20000000,
        ),
        TrialBalanceLine(
            dataset_id="ds-e2e",
            source_row_no=4,
            account_code="2010",
            account_name="Share Capital",
            closing_cr_paise=60000000,
        ),
        TrialBalanceLine(
            dataset_id="ds-e2e",
            source_row_no=5,
            account_code="2020",
            account_name="Trade Creditors",
            closing_cr_paise=40000000,
        ),
    ]
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(dataset)
        fin_repo.add_trial_balance_lines(tb_lines)

    # Step 2: Sync and Map All Accounts to Schedule III
    map_service.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng.id, dataset_id="ds-e2e")
    )

    map_service.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1010",
            schedule_iii_category="Property, Plant and Equipment",
            schedule_iii_line_item="Buildings",
            lead_schedule_ref="WP-D1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_service.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1020",
            schedule_iii_category="Trade Receivables",
            schedule_iii_line_item="Debtors",
            lead_schedule_ref="WP-G1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_service.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1030",
            schedule_iii_category="Cash and Cash Equivalents",
            schedule_iii_line_item="Bank",
            lead_schedule_ref="WP-H1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_service.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="2010",
            schedule_iii_category="Share Capital",
            schedule_iii_line_item="Equity",
            lead_schedule_ref="WP-A1",
            account_type=AccountTypeEnum.EQUITY,
        )
    )
    map_service.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="2020",
            schedule_iii_category="Trade Payables",
            schedule_iii_line_item="Creditors",
            lead_schedule_ref="WP-C2",
            account_type=AccountTypeEnum.LIABILITY,
        )
    )

    # Step 3: Validate Mappings Quality Gate
    report = map_service.validate_mappings(ValidateMappingsDTO(engagement_id=eng.id))
    assert report.is_valid_for_finalization is True
    assert report.material_unmapped_count == 0

    # Step 4: Create & Approve AJE #1 (Unrecorded Creditor: Dr PPE ₹5,00,000 (5,000,000 paise), Cr Creditors ₹5,00,000)
    SecurityContext.set_current_session(
        UserSession(user_id="user-assoc", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    aje1 = adj_service.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng.id,
            aje_number="AJE-001",
            entry_date="2026-03-31",
            title="Unrecorded Plant Invoice",
            narration="Invoice received post year-end for plant addition",
            reason="Cutoff omission",
            lines=[
                CreateAJELineDTO(
                    account_code="1010",
                    account_name="Factory Building",
                    debit_paise=5000000,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="2020",
                    account_name="Trade Creditors",
                    debit_paise=0,
                    credit_paise=5000000,
                ),
            ],
        )
    )
    adj_service.submit_adjustment(SubmitAJEDTO(engagement_id=eng.id, entry_id=aje1.id))
    SecurityContext.set_current_session(
        UserSession(user_id="user-mgr", username="mgr1", role=RoleEnum.MANAGER)
    )
    adj_service.review_adjustment(
        ReviewAJEDTO(engagement_id=eng.id, entry_id=aje1.id, decision="APPROVE")
    )

    # Step 5: Create & Approve AJE #2 (Bad Debt Provision: Dr Bank ₹2,00,000 (2,000,000 paise), Cr Debtors ₹2,00,000)
    SecurityContext.set_current_session(
        UserSession(user_id="user-assoc", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    aje2 = adj_service.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng.id,
            aje_number="AJE-002",
            entry_date="2026-03-31",
            title="Bad Debt Provision",
            narration="Specific provision for doubtful recovery",
            reason="Customer insolvent",
            lines=[
                CreateAJELineDTO(
                    account_code="1030",
                    account_name="HDFC Bank",
                    debit_paise=2000000,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="1020",
                    account_name="Trade Debtors",
                    debit_paise=0,
                    credit_paise=2000000,
                ),
            ],
        )
    )
    adj_service.submit_adjustment(SubmitAJEDTO(engagement_id=eng.id, entry_id=aje2.id))
    SecurityContext.set_current_session(
        UserSession(user_id="user-mgr", username="mgr1", role=RoleEnum.MANAGER)
    )
    adj_service.review_adjustment(
        ReviewAJEDTO(engagement_id=eng.id, entry_id=aje2.id, decision="APPROVE")
    )

    # Step 6: Calculate Adjusted Trial Balance
    adj_tb = adj_service.calculate_adjusted_trial_balance(eng.id, "ds-e2e")

    # Step 7: Verify Financial Invariants
    assert (
        adj_tb.is_unadjusted_balanced is True
    )  # Total Unadjusted Dr (1,00,00,000) == Cr (1,00,00,000)
    assert adj_tb.is_adjustments_balanced is True  # Total AJE Dr (7,00,000) == Cr (7,00,000)
    assert (
        adj_tb.is_adjusted_balanced is True
    )  # Total Adjusted Dr (1,05,00,000) == Cr (1,05,00,000)
    assert adj_tb.is_fully_balanced is True

    # Step 8: Verify Account-Specific Balances
    acc_map = {l.account_code: l for l in adj_tb.lines}
    # Factory Building: 50,00,000 + 5,00,000 = 55,00,000
    assert acc_map["1010"].adjusted_dr_paise == 55000000
    # Trade Debtors: 30,00,000 - 2,00,000 = 28,00,000
    assert acc_map["1020"].adjusted_dr_paise == 28000000
    # Trade Creditors: 40,00,000 + 5,00,000 = 45,00,000
    assert acc_map["2020"].adjusted_cr_paise == 45000000

    # Step 9: Verify Bi-Directional Lead Schedules Rollup
    lead_schedules = adj_service.calculate_lead_schedules(eng.id, "ds-e2e")
    assert len(lead_schedules) == 5

    ls_dict = {ls.lead_schedule_ref: ls for ls in lead_schedules}
    # WP-D1: PPE
    assert ls_dict["WP-D1"].adjusted_balance_paise == 55000000
    assert "AJE-001" in ls_dict["WP-D1"].accounts[0].linked_aje_numbers

    # WP-C2: Trade Payables
    assert ls_dict["WP-C2"].adjusted_balance_paise == 45000000
    assert "AJE-001" in ls_dict["WP-C2"].accounts[0].linked_aje_numbers

    # Invariant: Lead Schedule Sum == Component Account Sum
    for ls in lead_schedules:
        assert ls.adjusted_balance_paise == sum(a.adjusted_balance_paise for a in ls.accounts)


def test_large_dataset_scalability_benchmark(db_manager, seed_environment):
    """Performance test with 100, 1,000, 5,000, and 10,000 trial balance rows."""
    eng = seed_environment
    map_service = AccountMappingService(db_manager)
    adj_service = AuditAdjustmentService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-mgr", username="mgr1", role=RoleEnum.MANAGER)
    )

    row_counts = [100, 1000, 5000, 10000]
    timings = {}

    for count in row_counts:
        ds_id = f"ds-bench-{count}"
        dataset = FinancialDataset(
            id=ds_id,
            engagement_id=eng.id,
            dataset_name=f"Bench_{count}.xlsx",
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        )

        # Half debits, half credits balanced
        half = count // 2
        lines = []
        for i in range(1, half + 1):
            lines.append(
                TrialBalanceLine(
                    dataset_id=ds_id,
                    source_row_no=i,
                    account_code=f"DR_{i}",
                    account_name=f"Asset Account {i}",
                    closing_dr_paise=100000,
                )
            )
        for i in range(half + 1, count + 1):
            lines.append(
                TrialBalanceLine(
                    dataset_id=ds_id,
                    source_row_no=i,
                    account_code=f"CR_{i}",
                    account_name=f"Liability Account {i}",
                    closing_cr_paise=100000,
                )
            )

        # Ingestion
        t0 = time.perf_counter()
        with db_manager.session_scope() as session:
            fin_repo = FinancialDataRepository(session)
            fin_repo.add_dataset(dataset)
            fin_repo.add_trial_balance_lines(lines)
        t_ingest = time.perf_counter() - t0

        # Mapping Sync
        t0 = time.perf_counter()
        map_service.sync_trial_balance_accounts(
            SyncTrialBalanceAccountsDTO(engagement_id=eng.id, dataset_id=ds_id)
        )
        t_sync = time.perf_counter() - t0

        # Adjusted TB Calculation
        t0 = time.perf_counter()
        adj_tb = adj_service.calculate_adjusted_trial_balance(eng.id, ds_id)
        t_calc = time.perf_counter() - t0

        # Lead Schedule Rollup
        t0 = time.perf_counter()
        lead_schedules = adj_service.calculate_lead_schedules(eng.id, ds_id)
        t_ls = time.perf_counter() - t0

        timings[count] = {
            "ingest_s": round(t_ingest, 4),
            "sync_s": round(t_sync, 4),
            "calc_s": round(t_calc, 4),
            "lead_sched_s": round(t_ls, 4),
        }

        # Verify invariants for each scale
        assert adj_tb.is_fully_balanced is True
        assert len(adj_tb.lines) >= count
        assert len(lead_schedules) >= 1

    # Performance assertions: 10,000 rows calculation must take < 2.0s
    assert timings[10000]["calc_s"] < 2.0
    assert timings[10000]["lead_sched_s"] < 2.0
