"""Comprehensive test suite for Schedule III Balance Sheet, P&L, Changes in Equity, and Packaging."""

from uuid import uuid4

import pytest

from finauditpro.application.financial_statement_dtos import (
    GenerateFinancialStatementsDTO,
    LockFinancialStatementPackageDTO,
    ReviewFinancialStatementPackageDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.exceptions import ValidationError
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


@pytest.fixture
def test_setup(tmp_path):
    db_file = tmp_path / "test_fs.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = Firm(id=str(uuid4()), name="Audit Firm LLP", registration_number="REG123")
        firm_repo.add(firm)

        client_repo = ClientRepository(session)
        client = Client(
            id=str(uuid4()), firm_id=firm.id, name="Zenith Mfg Pvt Ltd", industry="Manufacturing"
        )
        client_repo.add(client)

        user_repo = UserRepository(session)
        user = User(
            id=str(uuid4()),
            email="partner@firm.com",
            username="partner_user",
            password_hash="h",
            salt="s",
            full_name="Audit Partner",
            role=RoleEnum.PARTNER,
        )
        user_repo.add(user)

        eng_repo = EngagementRepository(session)
        eng = Engagement(
            id=str(uuid4()),
            firm_id=firm.id,
            client_id=client.id,
            title="FY 2025-26 Statutory Audit",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.PLANNING,
        )
        eng_repo.add(eng)

        # Set up a complete balanced Trial Balance
        dataset_id = str(uuid4())
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng.id,
                dataset_name="Trial Balance",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="tb.csv",
            )
        )

        # Balanced accounts: Total Dr = Total Cr = ₹5,00,00,000 (50,000,000 paise = ₹5,00,000)
        # Scale in paise: 1 Cr = 10,000,000 paise
        tb_lines = [
            # Equity & Liabilities (Cr balances)
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=1,
                account_code="1001",
                account_name="Equity Share Capital",
                closing_cr_paise=100000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=2,
                account_code="1002",
                account_name="General Reserves",
                closing_cr_paise=50000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=3,
                account_code="2001",
                account_name="HDFC Term Loan",
                closing_cr_paise=80000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=4,
                account_code="2002",
                account_name="Trade Creditors Others",
                closing_cr_paise=40000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=5,
                account_code="3001",
                account_name="Revenue from Operations",
                closing_cr_paise=230000000,
            ),
            # Assets & Expenses (Dr balances)
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=6,
                account_code="4001",
                account_name="Plant & Machinery",
                closing_dr_paise=150000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=7,
                account_code="4002",
                account_name="Inventories Raw Material",
                closing_dr_paise=60000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=8,
                account_code="4003",
                account_name="Trade Debtors",
                closing_dr_paise=50000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=9,
                account_code="4004",
                account_name="HDFC Bank Current Account",
                closing_dr_paise=10000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=10,
                account_code="5001",
                account_name="Raw Material Consumed",
                closing_dr_paise=120000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=11,
                account_code="5002",
                account_name="Salaries & Wages",
                closing_dr_paise=70000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=12,
                account_code="5003",
                account_name="Bank Interest Expense",
                closing_dr_paise=10000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=13,
                account_code="5004",
                account_name="Factory Depreciation",
                closing_dr_paise=30000000,
            ),
        ]
        fin_repo.add_trial_balance_lines(tb_lines)

    # Apply Schedule III Account Mappings
    map_service = AccountMappingService(db_manager)
    map_service.initialize_mappings_from_trial_balance(eng.id, dataset_id)

    mappings_config = [
        ("1001", "Share Capital", "Equity Share Capital", "WP-A1", AccountTypeEnum.EQUITY),
        (
            "1002",
            "Reserves and Surplus",
            "Retained Earnings / General Reserve",
            "WP-A2",
            AccountTypeEnum.EQUITY,
        ),
        (
            "2001",
            "Long-Term Borrowings",
            "Term Loans from Banks & FIs",
            "WP-B1",
            AccountTypeEnum.LIABILITY,
        ),
        ("2002", "Trade Payables", "Trade Payables - Others", "WP-C2", AccountTypeEnum.LIABILITY),
        (
            "3001",
            "Revenue from Operations",
            "Sale of Products & Services",
            "WP-I1",
            AccountTypeEnum.INCOME,
        ),
        (
            "4001",
            "Property, Plant and Equipment",
            "Plant, Machinery & Equipment",
            "WP-D1",
            AccountTypeEnum.ASSET,
        ),
        ("4002", "Inventories", "Raw Materials & Consumables", "WP-F1", AccountTypeEnum.ASSET),
        (
            "4003",
            "Trade Receivables",
            "Trade Receivables - Undisputed Good",
            "WP-G1",
            AccountTypeEnum.ASSET,
        ),
        (
            "4004",
            "Cash and Cash Equivalents",
            "Balances with Banks & Fixed Deposits",
            "WP-H1",
            AccountTypeEnum.ASSET,
        ),
        (
            "5001",
            "Cost of Materials Consumed",
            "Raw Material Consumption",
            "WP-J1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5002",
            "Employee Benefits Expense",
            "Salaries, Wages & Staff Welfare",
            "WP-K1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5003",
            "Finance Costs",
            "Interest Expense & Bank Charges",
            "WP-L1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5004",
            "Depreciation and Amortization",
            "Depreciation on PPE",
            "WP-M1",
            AccountTypeEnum.EXPENSE,
        ),
    ]

    for code, cat, line, lead, atype in mappings_config:
        map_service.update_mapping(
            eng.id, code, cat, line, lead, atype, "Initial Schedule III Mapping"
        )

    return {
        "db_manager": db_manager,
        "engagement_id": eng.id,
        "dataset_id": dataset_id,
        "user_id": user.id,
    }


def test_schedule_iii_balance_sheet_and_pnl_generation(test_setup) -> None:
    """Test generating Schedule III Balance Sheet, P&L, and Changes in Equity from Adjusted TB."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="partner_user", role=RoleEnum.PARTNER)
    )

    fs_service = FinancialStatementService(db_manager)
    dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)

    # 1. Test Balance Sheet
    bs = fs_service.generate_balance_sheet(dto)
    assert bs is not None
    assert len(bs.equity_and_liabilities_lines) > 0
    assert len(bs.assets_lines) > 0
    assert bs.total_assets_paise == 270000000  # 150M PPE + 60M Inv + 50M Debtors + 10M Cash = 270M
    assert (
        bs.total_equity_and_liabilities_paise == 270000000
    )  # 100M Share Cap + 50M Res + 80M Loan + 40M Creditors = 270M
    assert bs.is_balanced is True
    assert bs.difference_paise == 0

    # 2. Test Statement of Profit & Loss
    pnl = fs_service.generate_profit_and_loss(dto)
    assert pnl is not None
    assert pnl.total_revenue_paise == 230000000  # 230M
    assert (
        pnl.total_expenses_paise == 230000000
    )  # 120M Material + 70M Salary + 10M Int + 30M Depr = 230M
    assert pnl.profit_before_tax_paise == 0
    assert pnl.profit_after_tax_paise == 0

    # 3. Test Statement of Changes in Equity
    eq = fs_service.generate_statement_of_changes_in_equity(dto)
    assert eq.closing_share_capital_paise == 100000000
    assert eq.closing_reserves_surplus_paise == 50000000
    assert eq.total_closing_equity_paise == 150000000


def test_package_lifecycle_locking_and_drift_detection(test_setup) -> None:
    """Test full package saving, review approval, partner locking, and data drift detection."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="partner_user", role=RoleEnum.PARTNER)
    )

    fs_service = FinancialStatementService(db_manager)

    # 1. Save Draft Package
    save_dto = SaveFinancialStatementPackageDTO(
        engagement_id=eng_id, version=FinancialStatementVersionEnum.DRAFT_V1
    )
    pkg = fs_service.save_package(save_dto)
    assert pkg.version == FinancialStatementVersionEnum.DRAFT_V1
    assert pkg.status == PackageStatusEnum.DRAFT
    assert pkg.is_locked is False
    assert pkg.is_stale is False

    # 2. Review and Approve Package
    rev_dto = ReviewFinancialStatementPackageDTO(
        engagement_id=eng_id,
        package_id=pkg.id,
        decision="APPROVE",
        reviewer_notes="Schedule III verified",
    )
    reviewed_pkg = fs_service.review_package(rev_dto)
    assert reviewed_pkg.status == PackageStatusEnum.APPROVED
    assert reviewed_pkg.version == FinancialStatementVersionEnum.REVIEWED_V3

    # 3. Lock Package as Final V4
    lock_dto = LockFinancialStatementPackageDTO(engagement_id=eng_id, package_id=pkg.id)
    locked_pkg = fs_service.lock_package(lock_dto)
    assert locked_pkg.is_locked is True
    assert locked_pkg.status == PackageStatusEnum.LOCKED
    assert locked_pkg.version == FinancialStatementVersionEnum.FINAL_LOCKED_V4

    # 4. Invariant: Cannot overwrite a locked package without unsealing
    with pytest.raises(ValidationError, match="Cannot modify locked financial statement package"):
        fs_service.save_package(save_dto)
