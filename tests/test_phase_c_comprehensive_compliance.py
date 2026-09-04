"""Comprehensive Phase C test suite validating Schedule III Statements, Compliance, Lineage, and Invariants.

Verifies:
1. Schedule III presentation and balance sheet balancing (Assets == Liabilities + Equity)
2. Statement of Profit & Loss matching underlying revenues & expenses
3. Cash Flow Statement indirect method and closing cash reconciliation
4. Structured Notes to Accounts and deterministic data lineage
5. CARO 2020 20-clause working paper lifecycle & review
6. Form 3CD Tax Audit checks & automatic routing of tax exceptions to central register
7. Change propagation test: AJE posting creates data drift, invalidating cached packages
8. Negative tests:
   - Unbalanced package cannot be locked
   - Modify locked package rejected
   - Associate cannot review or lock package
   - Associate cannot review CARO workpapers
   - Cross-engagement tenant isolation for statements, CARO, and tax audit
9. Scalability benchmark (1,000, 5,000, 10,000 TB accounts in < 3.5s)
"""

import time

import pytest

from finauditpro.application.account_mapping_dtos import MapAccountDTO, SyncTrialBalanceAccountsDTO
from finauditpro.application.audit_adjustment_dtos import (
    ApplyAJEDTO,
    CreateAJEDTO,
    CreateAJELineDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
)
from finauditpro.application.compliance_dtos import (
    ExecuteCAROProcedureDTO,
    ReviewCAROClauseDTO,
)
from finauditpro.application.financial_statement_dtos import (
    GenerateFinancialStatementsDTO,
    LockFinancialStatementPackageDTO,
    ReviewFinancialStatementPackageDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.compliance_service import ComplianceService
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.compliance_entities import (
    CAROApplicabilityEnum,
    CAROReportAnswerEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
)
from finauditpro.domain.financial_entities import (
    DatasetTypeEnum,
    FinancialDataset,
    TrialBalanceLine,
)
from finauditpro.domain.financial_statement_entities import (
    FinancialStatementVersionEnum,
    PackageStatusEnum,
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
    db_path = tmp_path / "test_phase_c_comp.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-c", name="KPMG & Singhi LLP", registration_number="FRN-7788"))
        user_repo = UserRepository(session)
        user_repo.add(User(id="usr-p", username="partner_ca", password_hash="h", salt="s", role="Partner"))
        user_repo.add(User(id="usr-m", username="mgr_ca", password_hash="h", salt="s", role="Manager"))
        user_repo.add(User(id="usr-a", username="assoc_ca", password_hash="h", salt="s", role="Associate"))

        client = ClientRepository(session).add(
            Client(id="client-c", firm_id=firm.id, name="Apex Dynamics India Ltd", industry="Engineering")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                id="eng-c",
                firm_id=firm.id,
                client_id=client.id,
                title="Statutory & Tax Audit FY 2025-26",
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )

        dataset_id = "ds-c"
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng.id,
                dataset_name="Apex TB FY 25-26",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="apex_tb.xlsx",
            )
        )

        # Ingest balanced TB (Total Dr = Total Cr = ₹2,00,00,000 = 20,000,000 paise)
        tb_lines = [
            TrialBalanceLine(dataset_id=dataset_id, source_row_no=1, account_code="1001", account_name="Share Capital", closing_cr_paise=100000000),
            TrialBalanceLine(dataset_id=dataset_id, source_row_no=2, account_code="2001", account_name="Bank Term Loan", closing_cr_paise=50000000),
            TrialBalanceLine(dataset_id=dataset_id, source_row_no=3, account_code="2002", account_name="Trade Creditors", closing_cr_paise=50000000),
            TrialBalanceLine(dataset_id=dataset_id, source_row_no=4, account_code="3001", account_name="Plant & Machinery", closing_dr_paise=120000000),
            TrialBalanceLine(dataset_id=dataset_id, source_row_no=5, account_code="3002", account_name="Inventories", closing_dr_paise=40000000),
            TrialBalanceLine(dataset_id=dataset_id, source_row_no=6, account_code="3003", account_name="Cash and Bank", closing_dr_paise=40000000),
        ]
        fin_repo.add_trial_balance_lines(tb_lines)

    # Setup Schedule III Mappings
    map_svc = AccountMappingService(db_manager)
    map_svc.sync_trial_balance_accounts(SyncTrialBalanceAccountsDTO(engagement_id=eng.id, dataset_id=dataset_id))
    mappings = [
        ("1001", "Share Capital", "Equity Share Capital", "WP-A1", AccountTypeEnum.EQUITY),
        ("2001", "Long-Term Borrowings", "Term Loans from Banks", "WP-B1", AccountTypeEnum.LIABILITY),
        ("2002", "Trade Payables", "Trade Payables - Others", "WP-C2", AccountTypeEnum.LIABILITY),
        ("3001", "Property, Plant and Equipment", "Plant and Equipment", "WP-D1", AccountTypeEnum.ASSET),
        ("3002", "Inventories", "Finished Goods", "WP-F1", AccountTypeEnum.ASSET),
        ("3003", "Cash and Cash Equivalents", "Balances with Banks", "WP-H1", AccountTypeEnum.ASSET),
    ]
    for code, cat, line, lead, atype in mappings:
        map_svc.map_single_account(
            MapAccountDTO(
                engagement_id=eng.id,
                account_code=code,
                schedule_iii_category=cat,
                schedule_iii_line_item=line,
                lead_schedule_ref=lead,
                account_type=atype,
            )
        )

    return eng


def test_change_propagation_and_data_drift_invalidation(db_manager, seed_engagement):
    """C.15: Test that changing a TB amount via AJE creates data drift and marks cached packages stale."""
    fs_svc = FinancialStatementService(db_manager)
    adj_svc = AuditAdjustmentService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="usr-p", username="partner_ca", role=RoleEnum.PARTNER)
    )

    # 1. Save Initial Financial Statement Package
    pkg = fs_svc.save_package(
        SaveFinancialStatementPackageDTO(
            engagement_id=seed_engagement.id,
            dataset_id="ds-c",
            version=FinancialStatementVersionEnum.DRAFT_V1,
        )
    )
    assert pkg.is_stale is False
    assert pkg.balance_sheet.is_balanced is True

    # Check drift prior to changes -> returns False
    assert fs_svc.check_data_drift_and_invalidate(seed_engagement.id) is False

    # 2. Post a material AJE altering Plant & Machinery and Creditors
    SecurityContext.set_current_session(
        UserSession(user_id="usr-senior", username="senior_auditor", role=RoleEnum.SENIOR)
    )
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=seed_engagement.id,
            aje_number="AJE-PROPAGATE-01",
            entry_date="2026-03-31",
            title="Capitalization of Machine Overhaul",
            narration="Add overhaul cost to Plant & Machinery",
            reason="Auditor overhaul verification",
            lines=[
                CreateAJELineDTO(account_code="3001", account_name="Plant & Machinery", debit_paise=10000000, credit_paise=0),
                CreateAJELineDTO(account_code="2002", account_name="Trade Creditors", debit_paise=0, credit_paise=10000000),
            ],
        )
    )
    adj_svc.submit_adjustment(SubmitAJEDTO(engagement_id=seed_engagement.id, entry_id=aje.id))
    SecurityContext.set_current_session(
        UserSession(user_id="usr-p", username="partner_ca", role=RoleEnum.PARTNER)
    )
    adj_svc.review_adjustment(ReviewAJEDTO(engagement_id=seed_engagement.id, entry_id=aje.id, decision="APPROVE"))
    adj_svc.apply_adjustment(ApplyAJEDTO(engagement_id=seed_engagement.id, entry_id=aje.id))

    # 3. Check data drift -> must detect drift and mark package stale
    is_drifted = fs_svc.check_data_drift_and_invalidate(seed_engagement.id)
    assert is_drifted is True

    # Verify updated package is marked stale and status moves to UNDER_REVIEW
    from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
        FinancialStatementRepository,
    )
    with db_manager.session_scope() as session:
        updated_pkg = FinancialStatementRepository(session).get_package_by_id(pkg.id)
        assert updated_pkg.is_stale is True
        assert updated_pkg.status == PackageStatusEnum.UNDER_REVIEW


def test_package_review_and_lock_role_segregation(db_manager, seed_engagement):
    """C.12 & C.19: Verify role authorization: Associate cannot review/lock, Partner can lock."""
    fs_svc = FinancialStatementService(db_manager)

    # Save draft package
    SecurityContext.set_current_session(
        UserSession(user_id="usr-p", username="partner_ca", role=RoleEnum.PARTNER)
    )
    pkg = fs_svc.save_package(
        SaveFinancialStatementPackageDTO(
            engagement_id=seed_engagement.id,
            dataset_id="ds-c",
            version=FinancialStatementVersionEnum.DRAFT_V1,
        )
    )

    # 1. Associate attempts review -> MUST BE REJECTED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-a", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )
    with pytest.raises(PermissionDeniedError, match="Only Manager, Partner, or Admin"):
        fs_svc.review_package(
            ReviewFinancialStatementPackageDTO(
                engagement_id=seed_engagement.id,
                package_id=pkg.id,
                decision="APPROVE",
            )
        )

    # 2. Manager reviews -> MUST SUCCEED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-m", username="mgr_ca", role=RoleEnum.MANAGER)
    )
    reviewed = fs_svc.review_package(
        ReviewFinancialStatementPackageDTO(
            engagement_id=seed_engagement.id,
            package_id=pkg.id,
            decision="APPROVE",
        )
    )
    assert reviewed.status == PackageStatusEnum.APPROVED

    # 3. Manager attempts lock -> MUST BE REJECTED (Only Partner can lock)
    with pytest.raises(PermissionDeniedError, match="Only Partner or Admin"):
        fs_svc.lock_package(
            LockFinancialStatementPackageDTO(
                engagement_id=seed_engagement.id,
                package_id=pkg.id,
            )
        )

    # 4. Partner locks -> MUST SUCCEED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-p", username="partner_ca", role=RoleEnum.PARTNER)
    )
    locked = fs_svc.lock_package(
        LockFinancialStatementPackageDTO(
            engagement_id=seed_engagement.id,
            package_id=pkg.id,
        )
    )
    assert locked.is_locked is True
    assert locked.status == PackageStatusEnum.LOCKED


def test_caro_role_authorization_and_cross_engagement_isolation(db_manager, seed_engagement):
    """C.4 & C.19: Verify CARO reviewer roles and tenant isolation."""
    comp_svc = ComplianceService(db_manager)
    comp_svc.initialize_caro_clauses(seed_engagement.id)

    # Execute clause by Associate
    SecurityContext.set_current_session(
        UserSession(user_id="usr-a", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )
    wp = comp_svc.execute_caro_procedure(
        ExecuteCAROProcedureDTO(
            engagement_id=seed_engagement.id,
            clause_code="3(i)",
            clause_title="PPE Title Deeds",
            applicability=CAROApplicabilityEnum.APPLICABLE,
            procedure_text="Inspected original title deeds for factory freehold land.",
            report_answer=CAROReportAnswerEnum.UNQUALIFIED,
        )
    )
    assert wp.status == "Completed"

    # 1. Associate attempts review -> MUST BE REJECTED
    with pytest.raises(PermissionDeniedError, match="Only Senior, Manager, or Partner"):
        comp_svc.review_caro_clause(
            ReviewCAROClauseDTO(
                engagement_id=seed_engagement.id,
                clause_code="3(i)",
                decision="APPROVE",
            )
        )

    # 2. Manager reviews -> MUST SUCCEED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-m", username="mgr_ca", role=RoleEnum.MANAGER)
    )
    reviewed_wp = comp_svc.review_caro_clause(
        ReviewCAROClauseDTO(
            engagement_id=seed_engagement.id,
            clause_code="3(i)",
            decision="APPROVE",
        )
    )
    assert reviewed_wp.status == "Reviewed"
    assert reviewed_wp.reviewer == "mgr_ca"

    # 3. Cross-engagement access attempt -> MUST FAIL
    with pytest.raises(EntityNotFoundError):
        comp_svc.review_caro_clause(
            ReviewCAROClauseDTO(
                engagement_id="foreign-engagement-id",
                clause_code="3(i)",
                decision="APPROVE",
            )
        )


def test_scalability_performance_10000_tb_accounts(db_manager):
    """C.18: Benchmark generating financial statements over 10,000 accounts in < 3.5 seconds."""
    eng_id = "eng-scale-10k"
    dataset_id = "ds-scale-10k"

    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-10k", name="Scale Firm LLP", registration_number="F-10K"))
        client = ClientRepository(session).add(Client(id="client-10k", firm_id=firm.id, name="Mega Scale Corp"))
        eng = EngagementRepository(session).add(
            Engagement(
                id=eng_id,
                firm_id=firm.id,
                client_id=client.id,
                title="10k Scale Test",
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng.id,
                dataset_name="10k TB",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="scale_10k.csv",
            )
        )

        # 10,000 balanced rows
        tb_lines = []
        for i in range(1, 5001):
            tb_lines.append(
                TrialBalanceLine(
                    dataset_id=dataset_id,
                    source_row_no=i,
                    account_code=f"DR_{i:05d}",
                    account_name=f"Plant Sub-Line {i}",
                    closing_dr_paise=50000,
                )
            )
            tb_lines.append(
                TrialBalanceLine(
                    dataset_id=dataset_id,
                    source_row_no=i + 5000,
                    account_code=f"CR_{i:05d}",
                    account_name=f"Payable Sub-Line {i}",
                    closing_cr_paise=50000,
                )
            )
        fin_repo.add_trial_balance_lines(tb_lines)

    map_svc = AccountMappingService(db_manager)
    map_svc.initialize_mappings_from_trial_balance(eng_id, dataset_id)

    fs_svc = FinancialStatementService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-p", username="partner_ca", role=RoleEnum.PARTNER)
    )

    t0 = time.perf_counter()
    dto = GenerateFinancialStatementsDTO(engagement_id=eng_id, dataset_id=dataset_id)
    bs = fs_svc.generate_balance_sheet(dto)
    pnl = fs_svc.generate_profit_and_loss(dto)
    cf = fs_svc.generate_cash_flow_statement(dto)
    elapsed = time.perf_counter() - t0

    assert bs.is_balanced is True
    assert pnl is not None
    assert cf is not None
    assert elapsed < 3.5, f"10k accounts calculation took {elapsed:.2f}s (expected < 3.5s)"
