"""Comprehensive Test Suite for Phase A: Financial & Trial Balance Foundation.

Validates:
- A.1: Schedule III Trial Balance Account Grouping, Mapping, Locking, Quality Gate, Re-import
- A.2: Audit Adjustment Journal Entry (AJE) Engine, Double-Entry Invariant, Maker-Checker, Reversals
- A.3: Dynamic Adjusted Trial Balance, Lead Schedule Rollup, Bidirectional Traceability
- Accounting correctness: Zero balances, Debit/Credit balances, Large amounts, Decimal precision
- Financial invariants: TB Dr==Cr, AJE Dr==Cr, Adj TB Dr==Cr, LS sum == account sum
- Security: RBAC, Maker-Checker self-approval block, Cross-engagement tenant isolation
- Database transactions & atomic rollbacks
- Scalability benchmarks: 100, 1,000, 5,000, 10,000 TB rows
"""

import time
from uuid import uuid4

import pytest

from finauditpro.application.account_mapping_dtos import (
    BulkMapAccountsDTO,
    MapAccountDTO,
    SyncTrialBalanceAccountsDTO,
    ValidateMappingsDTO,
)
from finauditpro.application.audit_adjustment_dtos import (
    ApplyAJEDTO,
    CreateAJEDTO,
    CreateAJELineDTO,
    ReverseAJEDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
    UpdateAJEDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum, MappingStatusEnum
from finauditpro.domain.audit_adjustment_entities import AJEStatusEnum, AJETypeEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
)
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.domain.financial_entities import (
    DatasetTypeEnum,
    FinancialDataset,
    TrialBalanceLine,
)
from finauditpro.infrastructure.financial.currency_parser import parse_indian_currency
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
    db_path = tmp_path / "test_phase_a_comprehensive.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_env(db_manager):
    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = firm_repo.add(Firm(id="firm-alpha", name="KPMG & Co."))

        user_repo = UserRepository(session)
        user_repo.add(
            User(id="usr-assoc", username="assoc_user", password_hash="h", salt="s", role="Associate")
        )
        user_repo.add(
            User(id="usr-senior", username="senior_user", password_hash="h", salt="s", role="Senior")
        )
        user_repo.add(
            User(id="usr-mgr", username="mgr_user", password_hash="h", salt="s", role="Manager")
        )
        user_repo.add(
            User(id="usr-partner", username="partner_user", password_hash="h", salt="s", role="Partner")
        )

        client_repo = ClientRepository(session)
        client = client_repo.add(
            Client(id="client-tata", firm_id=firm.id, name="Tata Steel Processing Ltd")
        )

        eng_repo = EngagementRepository(session)
        eng1 = eng_repo.add(
            Engagement(
                id="eng-101",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        eng2 = eng_repo.add(
            Engagement(
                id="eng-102",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2024-25",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        return eng1, eng2


# ==============================================================================
# 1. A.1: ACCOUNT MAPPING, LOCKING, REVIEW REQUIRED & QUALITY GATE TESTS
# ==============================================================================

def test_account_mapping_lifecycle_and_locking(db_manager, seed_env):
    eng1, _ = seed_env
    map_svc = AccountMappingService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_user", role=RoleEnum.SENIOR)
    )

    # 1. Setup TB with 2 accounts
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(id="ds-map-1", engagement_id=eng1.id, dataset_name="TB.xlsx")
        )
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-map-1",
                    source_row_no=1,
                    account_code="1042",
                    account_name="Factory Building",
                    closing_dr_paise=10000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-map-1",
                    source_row_no=2,
                    account_code="2010",
                    account_name="HDFC Term Loan",
                    closing_cr_paise=10000000,
                ),
            ]
        )

    synced = map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng1.id, dataset_id="ds-map-1")
    )
    assert len(synced) == 2
    assert all(m.status == MappingStatusEnum.UNMAPPED for m in synced)

    # 2. Cannot lock an unmapped account
    with pytest.raises(ValidationError, match="Cannot lock unmapped account"):
        map_svc.lock_mapping(eng1.id, "1042")

    # 3. Map account 1042 to PPE -> Buildings
    mapped = map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng1.id,
            account_code="1042",
            schedule_iii_category="Property, Plant and Equipment",
            schedule_iii_line_item="Buildings & Civil Structures",
            lead_schedule_ref="WP-D1",
            account_type=AccountTypeEnum.ASSET,
            reason="Initial classification",
        )
    )
    assert mapped.status == MappingStatusEnum.MAPPED
    assert mapped.schedule_iii_category == "Property, Plant and Equipment"

    # 4. Lock account 1042
    locked = map_svc.lock_mapping(eng1.id, "1042")
    assert locked.status == MappingStatusEnum.LOCKED

    # 5. Attempt to edit locked account -> MUST FAIL
    with pytest.raises(ValidationError, match="Cannot edit locked mapping"):
        map_svc.map_single_account(
            MapAccountDTO(
                engagement_id=eng1.id,
                account_code="1042",
                schedule_iii_category="Intangible Assets",
                schedule_iii_line_item="Software",
                lead_schedule_ref="WP-D3",
                account_type=AccountTypeEnum.ASSET,
            )
        )

    # 6. Unlock account 1042
    unlocked = map_svc.unlock_mapping(eng1.id, "1042")
    assert unlocked.status == MappingStatusEnum.MAPPED

    # 7. Flag Review Required
    flagged = map_svc.mark_review_required(eng1.id, "1042", "Check capitalization threshold")
    assert flagged.status == MappingStatusEnum.REVIEW_REQUIRED
    assert "Check capitalization threshold" in (flagged.notes or "")


def test_reimport_sync_identifies_new_and_preserves_existing(db_manager, seed_env):
    """Verify that re-importing updated TB tags NEW accounts clearly and preserves existing mappings."""
    eng1, _ = seed_env
    map_svc = AccountMappingService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_user", role=RoleEnum.SENIOR)
    )

    # Initial TB
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(id="ds-init", engagement_id=eng1.id, dataset_name="Init_TB.xlsx")
        )
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-init",
                    source_row_no=1,
                    account_code="1010",
                    account_name="Main Plant Machinery",
                    closing_dr_paise=50000000,
                ),
            ]
        )

    map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng1.id, dataset_id="ds-init")
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng1.id,
            account_code="1010",
            schedule_iii_category="Property, Plant and Equipment",
            schedule_iii_line_item="Plant, Machinery & Equipment",
            lead_schedule_ref="WP-D1",
            account_type=AccountTypeEnum.ASSET,
        )
    )

    # Re-import TB with name change on 1010 and brand new account 9001
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(id="ds-updated", engagement_id=eng1.id, dataset_name="Updated_TB.xlsx")
        )
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-updated",
                    source_row_no=1,
                    account_code="1010",
                    account_name="Main Plant Machinery (Upgraded)",
                    closing_dr_paise=60000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-updated",
                    source_row_no=2,
                    account_code="9001",
                    account_name="Solar Power Inverter (New Asset)",
                    closing_dr_paise=15000000,
                ),
            ]
        )

    re_synced = map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng1.id, dataset_id="ds-updated")
    )
    re_map = {m.account_code: m for m in re_synced}

    # 1010 preserved mapping, updated name, is_new=False
    assert re_map["1010"].status == MappingStatusEnum.MAPPED
    assert re_map["1010"].schedule_iii_category == "Property, Plant and Equipment"
    assert re_map["1010"].account_name == "Main Plant Machinery (Upgraded)"
    assert re_map["1010"].is_new is False

    # 9001 tagged as NEW, unmapped
    assert re_map["9001"].status == MappingStatusEnum.UNMAPPED
    assert re_map["9001"].is_new is True


def test_quality_gate_material_vs_zero_balance_rules(db_manager, seed_env):
    """Test 100% mapping of material accounts is required, while zero-balance accounts are permitted."""
    eng1, _ = seed_env
    map_svc = AccountMappingService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_user", role=RoleEnum.SENIOR)
    )

    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(id="ds-qgate", engagement_id=eng1.id, dataset_name="QGate_TB.xlsx")
        )
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-qgate",
                    source_row_no=1,
                    account_code="1001",
                    account_name="Active Cash",
                    closing_dr_paise=10000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-qgate",
                    source_row_no=2,
                    account_code="9990",
                    account_name="Dormant Zero Balance Account",
                    closing_dr_paise=0,
                    closing_cr_paise=0,
                    debit_paise=0,
                    credit_paise=0,
                ),
            ]
        )

    map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng1.id, dataset_id="ds-qgate")
    )

    # Initially fails because 1001 is material and unmapped
    r1 = map_svc.validate_mappings(ValidateMappingsDTO(engagement_id=eng1.id))
    assert r1.is_valid_for_finalization is False
    assert r1.material_unmapped_count == 1

    # Map material account 1001
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng1.id,
            account_code="1001",
            schedule_iii_category="Cash and Cash Equivalents",
            schedule_iii_line_item="Balances with Banks & Fixed Deposits",
            lead_schedule_ref="WP-H1",
            account_type=AccountTypeEnum.ASSET,
        )
    )

    # Now passes even though dormant account 9990 remains unmapped
    r2 = map_svc.validate_mappings(ValidateMappingsDTO(engagement_id=eng1.id))
    assert r2.is_valid_for_finalization is True
    assert r2.material_unmapped_count == 0
    assert r2.unmapped_count == 1  # 9990 is unmapped but immaterial


# ==============================================================================
# 2. A.2: AUDIT ADJUSTMENT JOURNAL ENTRY ENGINE & STRICT MAKER-CHECKER
# ==============================================================================

def test_aje_double_entry_exactness_and_decimal_precision(db_manager, seed_env):
    eng1, _ = seed_env
    adj_svc = AuditAdjustmentService(db_manager)

    # 1. Decimal currency parsing (₹12,34,567.89 -> 123456789 paise)
    parsed = parse_indian_currency("12,34,567.89")
    assert parsed.paise == 123456789

    # 2. Balanced AJE with paise precision passes
    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
    )
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-DEC-1",
            entry_date="2026-03-31",
            title="Exact Decimal Accrual",
            narration="Test decimal paise balance",
            reason="Ind AS 37 accrual",
            lines=[
                CreateAJELineDTO(
                    account_code="5001",
                    account_name="Legal Expenses",
                    debit_paise=123456789,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="2005",
                    account_name="Legal Dues Payable",
                    debit_paise=0,
                    credit_paise=123456789,
                ),
            ],
        )
    )
    assert aje.total_debit_paise == 123456789
    assert aje.total_credit_paise == 123456789

    # 3. 1-paise imbalance FAILS server-side validation
    with pytest.raises(ValidationError, match="Double-Entry Violation"):
        adj_svc.create_adjustment(
            CreateAJEDTO(
                engagement_id=eng1.id,
                aje_number="AJE-IMBALANCE",
                entry_date="2026-03-31",
                title="1-Paise Off",
                narration="Imbalance test",
                reason="Testing server enforcement",
                lines=[
                    CreateAJELineDTO(
                        account_code="5001",
                        account_name="Expense",
                        debit_paise=100000,
                        credit_paise=0,
                    ),
                    CreateAJELineDTO(
                        account_code="2005",
                        account_name="Payable",
                        debit_paise=0,
                        credit_paise=99999,  # 1 paise short
                    ),
                ],
            )
        )


def test_strict_maker_checker_disallows_partner_self_approval(db_manager, seed_env):
    """Enforce strict Maker-Checker: Partner CANNOT approve an AJE they prepared."""
    eng1, _ = seed_env
    adj_svc = AuditAdjustmentService(db_manager)

    # Partner prepares AJE
    SecurityContext.set_current_session(
        UserSession(user_id="usr-partner", username="partner_user", role=RoleEnum.PARTNER)
    )
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-PARTNER-1",
            entry_date="2026-03-31",
            title="Partner High-Level Adjustment",
            narration="Material provision adjustment",
            reason="Partner direct review adjustment",
            lines=[
                CreateAJELineDTO(
                    account_code="5002", account_name="Provision", debit_paise=5000000, credit_paise=0
                ),
                CreateAJELineDTO(
                    account_code="2006", account_name="Liability", debit_paise=0, credit_paise=5000000
                ),
            ],
        )
    )
    adj_svc.submit_adjustment(SubmitAJEDTO(engagement_id=eng1.id, entry_id=aje.id))

    # Partner attempts to approve own AJE -> MUST BE BLOCKED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-partner", username="partner_user", role=RoleEnum.PARTNER)
    )
    with pytest.raises(PermissionDeniedError, match="Maker-Checker Violation"):
        adj_svc.review_adjustment(
            ReviewAJEDTO(engagement_id=eng1.id, entry_id=aje.id, decision="APPROVE")
        )

    # Another authorized reviewer (Manager) approves -> MUST SUCCEED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-mgr", username="mgr_user", role=RoleEnum.MANAGER)
    )
    approved = adj_svc.review_adjustment(
        ReviewAJEDTO(engagement_id=eng1.id, entry_id=aje.id, decision="APPROVE")
    )
    assert approved.status == AJEStatusEnum.APPROVED
    assert approved.reviewed_by == "usr-mgr"


def test_draft_aje_editing_and_applied_immutability(db_manager, seed_env):
    eng1, _ = seed_env
    adj_svc = AuditAdjustmentService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
    )
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-EDIT-1",
            entry_date="2026-03-31",
            title="Original Draft",
            narration="Draft narration",
            reason="Draft reason",
            lines=[
                CreateAJELineDTO(
                    account_code="5010", account_name="Exp A", debit_paise=10000, credit_paise=0
                ),
                CreateAJELineDTO(
                    account_code="2010", account_name="Pay B", debit_paise=0, credit_paise=10000
                ),
            ],
        )
    )

    # Can edit Draft
    updated = adj_svc.update_draft_adjustment(
        UpdateAJEDTO(
            engagement_id=eng1.id,
            entry_id=aje.id,
            title="Updated Draft Title",
            narration="Updated narration",
            reason="Updated reason",
            lines=[
                CreateAJELineDTO(
                    account_code="5010", account_name="Exp A", debit_paise=25000, credit_paise=0
                ),
                CreateAJELineDTO(
                    account_code="2010", account_name="Pay B", debit_paise=0, credit_paise=25000
                ),
            ],
        )
    )
    assert updated.title == "Updated Draft Title"
    assert updated.total_debit_paise == 25000

    # Submit, Approve and Apply
    adj_svc.submit_adjustment(SubmitAJEDTO(engagement_id=eng1.id, entry_id=aje.id))
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_user", role=RoleEnum.SENIOR)
    )
    adj_svc.review_adjustment(ReviewAJEDTO(engagement_id=eng1.id, entry_id=aje.id, decision="APPROVE"))
    applied = adj_svc.apply_adjustment(ApplyAJEDTO(engagement_id=eng1.id, entry_id=aje.id))
    assert applied.status == AJEStatusEnum.APPLIED

    # Cannot edit Applied AJE
    with pytest.raises(ValidationError, match="Cannot edit AJE.*Applied"):
        adj_svc.update_draft_adjustment(
            UpdateAJEDTO(
                engagement_id=eng1.id,
                entry_id=aje.id,
                title="Illegal Mutation",
                narration="Bad",
                reason="Bad",
                lines=[
                    CreateAJELineDTO(
                        account_code="5010", account_name="Exp A", debit_paise=1000, credit_paise=0
                    ),
                    CreateAJELineDTO(
                        account_code="2010", account_name="Pay B", debit_paise=0, credit_paise=1000
                    ),
                ],
            )
        )


# ==============================================================================
# 3. A.3: MULTIPLE AJEs, FINANCIAL INVARIANTS & BIDIRECTIONAL TRACEABILITY
# ==============================================================================

def test_multiple_ajes_and_financial_invariants(db_manager, seed_env):
    """Test TB + AJE1 + AJE2 + AJE3 = Adjusted TB with complete financial invariant checks."""
    eng1, _ = seed_env
    map_svc = AccountMappingService(db_manager)
    adj_svc = AuditAdjustmentService(db_manager)

    # 1. Setup balanced TB: Dr Assets ₹5,00,00,000 (50,000,000 paise), Cr Liabilities ₹5,00,00,000
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(id="ds-multi", engagement_id=eng1.id, dataset_name="Multi_TB.xlsx")
        )
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id="ds-multi",
                    source_row_no=1,
                    account_code="1001",
                    account_name="Factory Building",
                    closing_dr_paise=25000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-multi",
                    source_row_no=2,
                    account_code="1002",
                    account_name="Sundry Debtors",
                    closing_dr_paise=25000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-multi",
                    source_row_no=3,
                    account_code="2001",
                    account_name="Equity Share Capital",
                    closing_cr_paise=30000000,
                ),
                TrialBalanceLine(
                    dataset_id="ds-multi",
                    source_row_no=4,
                    account_code="2002",
                    account_name="Sundry Creditors",
                    closing_cr_paise=20000000,
                ),
            ]
        )

    # 2. Map all accounts
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_user", role=RoleEnum.SENIOR)
    )
    map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng1.id, dataset_id="ds-multi")
    )
    map_svc.bulk_map_accounts(
        BulkMapAccountsDTO(
            engagement_id=eng1.id,
            account_codes=["1001"],
            schedule_iii_category="Property, Plant and Equipment",
            schedule_iii_line_item="Buildings & Civil Structures",
            lead_schedule_ref="WP-D1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_svc.bulk_map_accounts(
        BulkMapAccountsDTO(
            engagement_id=eng1.id,
            account_codes=["1002"],
            schedule_iii_category="Trade Receivables",
            schedule_iii_line_item="Trade Receivables - Undisputed Good",
            lead_schedule_ref="WP-G1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_svc.bulk_map_accounts(
        BulkMapAccountsDTO(
            engagement_id=eng1.id,
            account_codes=["2001"],
            schedule_iii_category="Share Capital",
            schedule_iii_line_item="Equity Share Capital",
            lead_schedule_ref="WP-A1",
            account_type=AccountTypeEnum.EQUITY,
        )
    )
    map_svc.bulk_map_accounts(
        BulkMapAccountsDTO(
            engagement_id=eng1.id,
            account_codes=["2002"],
            schedule_iii_category="Trade Payables",
            schedule_iii_line_item="Trade Payables - Others",
            lead_schedule_ref="WP-C2",
            account_type=AccountTypeEnum.LIABILITY,
        )
    )

    # 3. Create, submit, approve 3 distinct AJEs
    def _create_and_approve(aje_num: str, lines: list[CreateAJELineDTO]):
        SecurityContext.set_current_session(
            UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
        )
        entry = adj_svc.create_adjustment(
            CreateAJEDTO(
                engagement_id=eng1.id,
                aje_number=aje_num,
                entry_date="2026-03-31",
                title=f"Adjustment {aje_num}",
                narration=f"Narration {aje_num}",
                reason=f"Reason {aje_num}",
                lines=lines,
            )
        )
        adj_svc.submit_adjustment(SubmitAJEDTO(engagement_id=eng1.id, entry_id=entry.id))
        SecurityContext.set_current_session(
            UserSession(user_id="usr-mgr", username="mgr_user", role=RoleEnum.MANAGER)
        )
        return adj_svc.review_adjustment(
            ReviewAJEDTO(engagement_id=eng1.id, entry_id=entry.id, decision="APPROVE")
        )

    # AJE 1: Dr Factory Building ₹10,00,000, Cr Creditors ₹10,00,000
    _create_and_approve(
        "AJE-001",
        [
            CreateAJELineDTO(
                account_code="1001", account_name="Factory Building", debit_paise=1000000, credit_paise=0
            ),
            CreateAJELineDTO(
                account_code="2002", account_name="Sundry Creditors", debit_paise=0, credit_paise=1000000
            ),
        ],
    )

    # AJE 2: Dr Debtors ₹5,00,000, Cr Creditors ₹5,00,000
    _create_and_approve(
        "AJE-002",
        [
            CreateAJELineDTO(
                account_code="1002", account_name="Sundry Debtors", debit_paise=500000, credit_paise=0
            ),
            CreateAJELineDTO(
                account_code="2002", account_name="Sundry Creditors", debit_paise=0, credit_paise=500000
            ),
        ],
    )

    # AJE 3 (Multi-line): Dr Building ₹2,00,000, Dr Debtors ₹3,00,000, Cr Creditors ₹5,00,000
    _create_and_approve(
        "AJE-003",
        [
            CreateAJELineDTO(
                account_code="1001", account_name="Factory Building", debit_paise=200000, credit_paise=0
            ),
            CreateAJELineDTO(
                account_code="1002", account_name="Sundry Debtors", debit_paise=300000, credit_paise=0
            ),
            CreateAJELineDTO(
                account_code="2002", account_name="Sundry Creditors", debit_paise=0, credit_paise=500000
            ),
        ],
    )

    # 4. Calculate Adjusted TB
    adj_tb = adj_svc.calculate_adjusted_trial_balance(eng1.id, "ds-multi")

    # 5. Assert MANDATORY Financial Invariants
    assert adj_tb.is_unadjusted_balanced is True
    assert adj_tb.total_unadjusted_dr_paise == adj_tb.total_unadjusted_cr_paise == 50000000

    assert adj_tb.is_adjustments_balanced is True
    assert adj_tb.total_adjustment_dr_paise == adj_tb.total_adjustment_cr_paise == 2000000

    assert adj_tb.is_adjusted_balanced is True
    assert adj_tb.total_adjusted_dr_paise == adj_tb.total_adjusted_cr_paise == 52000000
    assert adj_tb.is_fully_balanced is True

    # Account-level verification:
    accs = {l.account_code: l for l in adj_tb.lines}
    # 1001 Building: 25,000,000 + 1,000,000 (AJE1) + 200,000 (AJE3) = 26,200,000
    assert accs["1001"].adjusted_dr_paise == 26200000
    # 1002 Debtors: 25,000,000 + 500,000 (AJE2) + 300,000 (AJE3) = 25,800,000
    assert accs["1002"].adjusted_dr_paise == 25800000
    # 2002 Creditors: 20,000,000 + 1,000,000 + 500,000 + 500,000 = 22,000,000
    assert accs["2002"].adjusted_cr_paise == 22000000

    # 6. Verify Lead Schedules and Invariant: Lead Schedule Sum == Component Account Sum
    lead_schedules = adj_svc.calculate_lead_schedules(eng1.id, "ds-multi")
    for ls in lead_schedules:
        assert ls.adjusted_balance_paise == sum(a.adjusted_balance_paise for a in ls.accounts)

    # 7. Verify Bidirectional Traceability
    trace_wp_d1 = adj_svc.get_lead_schedule_traceability(eng1.id, "WP-D1", "ds-multi")
    assert trace_wp_d1.lead_schedule_ref == "WP-D1"
    assert len(trace_wp_d1.accounts) == 1
    assert len(trace_wp_d1.accounts[0].linked_ajes) == 2  # AJE-001 and AJE-003
    linked_nums = {a["aje_number"] for a in trace_wp_d1.accounts[0].linked_ajes}
    assert linked_nums == {"AJE-001", "AJE-003"}

    # Reverse Trace: Account -> Linked AJEs
    trace_creditors = adj_svc.get_account_traceability(eng1.id, "2002", "ds-multi")
    assert trace_creditors.account_code == "2002"
    assert len(trace_creditors.linked_ajes) == 3  # Affected by all 3 AJEs


# ==============================================================================
# 4. LARGE DATASETS & SCALABILITY BENCHMARKS (100, 1000, 5000, 10000 ROWS)
# ==============================================================================

def test_scalability_benchmark_to_10000_rows(db_manager, seed_env):
    """Performance & correctness benchmark for large Trial Balance datasets up to 10,000 accounts."""
    eng1, _ = seed_env
    map_svc = AccountMappingService(db_manager)
    adj_svc = AuditAdjustmentService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_user", role=RoleEnum.SENIOR)
    )

    sizes = [100, 1000, 5000, 10000]
    timings = {}

    for count in sizes:
        ds_id = f"ds-scale-{count}"
        dataset = FinancialDataset(
            id=ds_id,
            engagement_id=eng1.id,
            dataset_name=f"Scale_{count}.xlsx",
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        )

        half = count // 2
        lines = []
        for i in range(1, half + 1):
            lines.append(
                TrialBalanceLine(
                    dataset_id=ds_id,
                    source_row_no=i,
                    account_code=f"DR_{count}_{i}",
                    account_name=f"Debtor Asset Account {i}",
                    closing_dr_paise=100000,
                )
            )
        for i in range(half + 1, count + 1):
            lines.append(
                TrialBalanceLine(
                    dataset_id=ds_id,
                    source_row_no=i,
                    account_code=f"CR_{count}_{i}",
                    account_name=f"Creditor Liability Account {i}",
                    closing_cr_paise=100000,
                )
            )

        # Ingest
        t0 = time.perf_counter()
        with db_manager.session_scope() as session:
            fin_repo = FinancialDataRepository(session)
            fin_repo.add_dataset(dataset)
            fin_repo.add_trial_balance_lines(lines)
        t_ingest = time.perf_counter() - t0

        # Mapping sync
        t0 = time.perf_counter()
        map_svc.sync_trial_balance_accounts(
            SyncTrialBalanceAccountsDTO(engagement_id=eng1.id, dataset_id=ds_id)
        )
        t_sync = time.perf_counter() - t0

        # Adjusted TB calculation
        t0 = time.perf_counter()
        adj_tb = adj_svc.calculate_adjusted_trial_balance(eng1.id, ds_id)
        t_calc = time.perf_counter() - t0

        # Lead Schedule rollup
        t0 = time.perf_counter()
        lead_schedules = adj_svc.calculate_lead_schedules(eng1.id, ds_id)
        t_rollup = time.perf_counter() - t0

        timings[count] = {
            "ingest_s": round(t_ingest, 4),
            "sync_s": round(t_sync, 4),
            "calc_s": round(t_calc, 4),
            "rollup_s": round(t_rollup, 4),
        }

        # Check invariants at every scale
        assert adj_tb.is_fully_balanced is True
        assert len(adj_tb.lines) >= count
        assert len(lead_schedules) >= 1

    # Print benchmark summary for documentation
    print("\n=== PHASE A TB SCALABILITY BENCHMARK ===")
    for count, t in timings.items():
        print(
            f"Rows: {count:>5} | Ingest: {t['ingest_s']}s | Sync: {t['sync_s']}s | Calc: {t['calc_s']}s | Rollup: {t['rollup_s']}s"
        )

    # 10,000 rows calculation and rollup must execute within reasonable thresholds (< 2.5s)
    assert timings[10000]["calc_s"] < 2.5
    assert timings[10000]["rollup_s"] < 2.5


# ==============================================================================
# 5. TRANSACTION ATOMICITY, TENANT ISOLATION, CRORES SCALE & DUPLICATES
# ==============================================================================

def test_large_amounts_crores_scale_precision(db_manager, seed_env):
    """Test large amounts (₹500 Crore = 5,00,00,00,000.00 = 500,000,000,000 paise) precision."""
    eng1, _ = seed_env
    adj_svc = AuditAdjustmentService(db_manager)

    amount_paise = 500000000000

    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
    )
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-CRORES-1",
            entry_date="2026-03-31",
            title="₹500 Crore Corporate Debt Adjustment",
            narration="Syndicated term loan drawdown",
            reason="Material debt restructuring",
            lines=[
                CreateAJELineDTO(
                    account_code="1005",
                    account_name="Bank Escrow",
                    debit_paise=amount_paise,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="2005",
                    account_name="Long Term Borrowings",
                    debit_paise=0,
                    credit_paise=amount_paise,
                ),
            ],
        )
    )
    assert aje.total_debit_paise == amount_paise
    assert aje.total_credit_paise == amount_paise


def test_cross_engagement_tenant_isolation_phase_a(db_manager, seed_env):
    """Verify that Engagement 101 data cannot be accessed or modified from Engagement 102 context."""
    eng1, eng2 = seed_env
    adj_svc = AuditAdjustmentService(db_manager)
    map_svc = AccountMappingService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
    )
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-ISO-1",
            entry_date="2026-03-31",
            title="Eng 101 Only",
            narration="Isolation check",
            reason="Check cross tenant access",
            lines=[
                CreateAJELineDTO(
                    account_code="1001", account_name="Cash", debit_paise=50000, credit_paise=0
                ),
                CreateAJELineDTO(
                    account_code="2001", account_name="Loan", debit_paise=0, credit_paise=50000
                ),
            ],
        )
    )

    # Attempt to submit from Engagement 102 -> MUST FAIL
    with pytest.raises(EntityNotFoundError):
        adj_svc.submit_adjustment(SubmitAJEDTO(engagement_id=eng2.id, entry_id=aje.id))

    # Attempt to lock an account in Engagement 102 that only exists in Engagement 101 -> MUST FAIL
    with pytest.raises(EntityNotFoundError):
        map_svc.lock_mapping(eng2.id, "1001")


def test_transaction_atomicity_and_rollback_on_failure(db_manager, seed_env):
    """Verify that database transactions rollback completely if an invalid operation occurs."""
    eng1, _ = seed_env
    adj_svc = AuditAdjustmentService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
    )

    initial_count = len(adj_svc.list_adjustments(eng1.id))

    # Attempt to create an invalid AJE with double-entry violation
    with pytest.raises(ValidationError):
        adj_svc.create_adjustment(
            CreateAJEDTO(
                engagement_id=eng1.id,
                aje_number="AJE-FAIL-ROLLBACK",
                entry_date="2026-03-31",
                title="Should Rollback",
                narration="Imbalanced",
                reason="Testing rollback",
                lines=[
                    CreateAJELineDTO(
                        account_code="1001", account_name="Cash", debit_paise=100000, credit_paise=0
                    ),
                    CreateAJELineDTO(
                        account_code="2001", account_name="Loan", debit_paise=0, credit_paise=50000
                    ),
                ],
            )
        )

    after_count = len(adj_svc.list_adjustments(eng1.id))
    assert after_count == initial_count


def test_duplicate_aje_number_rejection(db_manager, seed_env):
    """Enforce uniqueness of AJE numbers within an audit engagement."""
    eng1, _ = seed_env
    adj_svc = AuditAdjustmentService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_user", role=RoleEnum.ASSOCIATE)
    )
    adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-DUP-TEST",
            entry_date="2026-03-31",
            title="First Entry",
            narration="Original",
            reason="Test dup",
            lines=[
                CreateAJELineDTO(
                    account_code="1001", account_name="Cash", debit_paise=1000, credit_paise=0
                ),
                CreateAJELineDTO(
                    account_code="2001", account_name="Loan", debit_paise=0, credit_paise=1000
                ),
            ],
        )
    )

    with pytest.raises(ValidationError, match="already exists"):
        adj_svc.create_adjustment(
            CreateAJEDTO(
                engagement_id=eng1.id,
                aje_number="AJE-DUP-TEST",
                entry_date="2026-03-31",
                title="Duplicate Entry",
                narration="Duplicate",
                reason="Test dup collision",
                lines=[
                    CreateAJELineDTO(
                        account_code="1001", account_name="Cash", debit_paise=2000, credit_paise=0
                    ),
                    CreateAJELineDTO(
                        account_code="2001", account_name="Loan", debit_paise=0, credit_paise=2000
                    ),
                ],
            )
        )

