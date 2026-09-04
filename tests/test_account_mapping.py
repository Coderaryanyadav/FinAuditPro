"""Tests for Schedule III Account Mapping, Taxonomies, History Tracking, and Re-import Synchronization."""

import pytest

from finauditpro.application.account_mapping_dtos import (
    BulkMapAccountsDTO,
    MapAccountDTO,
    SyncTrialBalanceAccountsDTO,
    ValidateMappingsDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum, MappingStatusEnum
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
    db_path = tmp_path / "test_mapping.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = firm_repo.add(Firm(id="firm-1", name="CA Audit Firm"))

        user_repo = UserRepository(session)
        user_repo.add(
            User(id="user-auditor", username="auditor1", password_hash="h", salt="s", role="Senior")
        )
        user_repo.add(
            User(
                id="user-partner", username="partner1", password_hash="h", salt="s", role="Partner"
            )
        )

        client_repo = ClientRepository(session)
        client = client_repo.add(
            Client(id="client-1", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        )

        eng_repo = EngagementRepository(session)
        eng = eng_repo.add(
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


def test_taxonomy_retrieval(db_manager):
    service = AccountMappingService(db_manager)
    taxonomy = service.get_taxonomy()
    assert len(taxonomy) >= 20
    assert any(
        h.category == "Property, Plant and Equipment"
        and h.line_item == "Buildings & Civil Structures"
        for h in taxonomy
    )
    assert any(
        h.category == "Trade Payables" and h.line_item == "Trade Payables - MSME" for h in taxonomy
    )


def test_sync_trial_balance_and_reimport_preservation(db_manager, seed_engagement):
    service = AccountMappingService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # 1. Ingest Initial TB with 3 accounts
    dataset_1 = FinancialDataset(
        id="ds-1",
        engagement_id=seed_engagement.id,
        dataset_name="Initial_TB.xlsx",
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
    )
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(dataset_1)
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-1",
                    source_row_no=1,
                    account_code="1010",
                    account_name="Factory Building",
                    closing_dr_paise=50000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-1",
                    source_row_no=2,
                    account_code="2010",
                    account_name="Term Loan HDFC",
                    closing_cr_paise=30000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-1",
                    source_row_no=3,
                    account_code="9999",
                    account_name="Zero Balance Memo",
                    closing_dr_paise=0,
                    closing_cr_paise=0,
                ),
            ]
        )

    synced = service.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=seed_engagement.id, dataset_id="ds-1")
    )
    assert len(synced) == 3
    assert all(m.status == MappingStatusEnum.UNMAPPED for m in synced)

    # 2. Map Account 1010 to PPE
    service.map_single_account(
        MapAccountDTO(
            engagement_id=seed_engagement.id,
            account_code="1010",
            schedule_iii_category="Property, Plant and Equipment",
            schedule_iii_line_item="Buildings & Civil Structures",
            lead_schedule_ref="WP-D1",
            account_type=AccountTypeEnum.ASSET,
        )
    )

    # 3. Re-import Updated TB with 1 new account (3010) and updated 1010/2010
    dataset_2 = FinancialDataset(
        id="ds-2",
        engagement_id=seed_engagement.id,
        dataset_name="Updated_TB.xlsx",
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
    )
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(dataset_2)
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-2",
                    source_row_no=1,
                    account_code="1010",
                    account_name="Factory Building (Renovated)",
                    closing_dr_paise=55000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-2",
                    source_row_no=2,
                    account_code="2010",
                    account_name="Term Loan HDFC",
                    closing_cr_paise=30000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-2",
                    source_row_no=3,
                    account_code="3010",
                    account_name="New Raw Material Stock",
                    closing_dr_paise=15000000,
                ),
            ]
        )

    re_synced = service.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=seed_engagement.id, dataset_id="ds-2")
    )
    assert len(re_synced) >= 3
    all_mappings = {m.account_code: m for m in service.list_mappings(seed_engagement.id)}

    # Verify Account 1010 preserved its MAPPED status and updated name
    assert all_mappings["1010"].status == MappingStatusEnum.MAPPED
    assert all_mappings["1010"].schedule_iii_category == "Property, Plant and Equipment"
    assert all_mappings["1010"].account_name == "Factory Building (Renovated)"

    # Verify Account 3010 is clearly tagged as NEW and UNMAPPED
    assert all_mappings["3010"].is_new is True
    assert all_mappings["3010"].status == MappingStatusEnum.UNMAPPED


def test_bulk_account_mapping_and_audit_history(db_manager, seed_engagement):
    service = AccountMappingService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # Ingest 3 debtors
    dataset = FinancialDataset(
        id="ds-debtors", engagement_id=seed_engagement.id, dataset_name="Debtors.xlsx"
    )
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(dataset)
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-debtors",
                    source_row_no=1,
                    account_code="CUST-001",
                    account_name="Reliance Retail",
                    closing_dr_paise=10000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-debtors",
                    source_row_no=2,
                    account_code="CUST-002",
                    account_name="Tata Motors",
                    closing_dr_paise=20000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-debtors",
                    source_row_no=3,
                    account_code="CUST-003",
                    account_name="L&T Infotech",
                    closing_dr_paise=15000000,
                ),
            ]
        )

    service.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=seed_engagement.id, dataset_id="ds-debtors")
    )

    # Bulk map all 3 to Trade Receivables
    bulk_result = service.bulk_map_accounts(
        BulkMapAccountsDTO(
            engagement_id=seed_engagement.id,
            account_codes=["CUST-001", "CUST-002", "CUST-003"],
            schedule_iii_category="Trade Receivables",
            schedule_iii_line_item="Trade Receivables - Undisputed Good",
            lead_schedule_ref="WP-G1",
            account_type=AccountTypeEnum.ASSET,
            reason="Bulk customer classification",
        )
    )
    assert len(bulk_result) == 3
    assert all(m.status == MappingStatusEnum.MAPPED for m in bulk_result)

    # Check Audit Trail History for CUST-001
    cust_1 = bulk_result[0]
    history = service.get_mapping_history(cust_1.id)
    assert len(history) >= 1
    assert history[0].new_category == "Trade Receivables"
    assert history[0].changed_by == "user-auditor"


def test_mapping_validation_quality_gate(db_manager, seed_engagement):
    service = AccountMappingService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    dataset = FinancialDataset(
        id="ds-val", engagement_id=seed_engagement.id, dataset_name="TB.xlsx"
    )
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(dataset)
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-val",
                    source_row_no=1,
                    account_code="1001",
                    account_name="Cash on Hand",
                    closing_dr_paise=500000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-val",
                    source_row_no=2,
                    account_code="1002",
                    account_name="HDFC Bank",
                    closing_dr_paise=1500000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-val",
                    source_row_no=3,
                    account_code="9999",
                    account_name="Zero Balance Account",
                    closing_dr_paise=0,
                    closing_cr_paise=0,
                ),
            ]
        )

    service.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=seed_engagement.id, dataset_id="ds-val")
    )

    # Initial validation should FAIL (material accounts 1001 and 1002 are unmapped)
    report_initial = service.validate_mappings(
        ValidateMappingsDTO(engagement_id=seed_engagement.id)
    )
    assert report_initial.is_valid_for_finalization is False
    assert report_initial.material_unmapped_count == 2

    # Map material accounts
    service.bulk_map_accounts(
        BulkMapAccountsDTO(
            engagement_id=seed_engagement.id,
            account_codes=["1001", "1002"],
            schedule_iii_category="Cash and Cash Equivalents",
            schedule_iii_line_item="Balances with Banks & Fixed Deposits",
            lead_schedule_ref="WP-H1",
            account_type=AccountTypeEnum.ASSET,
        )
    )

    # Validation should now PASS (even with 0-balance account 9999 unmapped)
    report_passed = service.validate_mappings(ValidateMappingsDTO(engagement_id=seed_engagement.id))
    assert report_passed.is_valid_for_finalization is True
    assert report_passed.material_unmapped_count == 0
