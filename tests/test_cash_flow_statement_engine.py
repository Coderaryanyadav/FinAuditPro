"""Comprehensive test suite for Cash Flow Statement engine and strict cash reconciliations."""

from uuid import uuid4

import pytest

from finauditpro.application.financial_statement_dtos import GenerateFinancialStatementsDTO
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


@pytest.fixture
def test_setup(tmp_path):
    db_file = tmp_path / "test_cf.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = Firm(id=str(uuid4()), name="Audit Firm LLP", registration_number="REG123")
        firm_repo.add(firm)

        client_repo = ClientRepository(session)
        client = Client(
            id=str(uuid4()),
            firm_id=firm.id,
            name="CashFlow Client Pvt Ltd",
            industry="Manufacturing",
        )
        client_repo.add(client)

        user_repo = UserRepository(session)
        user = User(
            id=str(uuid4()),
            email="senior@firm.com",
            username="senior_user",
            password_hash="h",
            salt="s",
            full_name="Senior Auditor",
            role=RoleEnum.SENIOR,
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

        # TB setup with positive Net Profit
        tb_lines = [
            # Equity & Liabilities
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
                account_name="Reserves & Surplus",
                closing_cr_paise=30000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=3,
                account_code="2001",
                account_name="Term Loan from Bank",
                closing_cr_paise=50000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=4,
                account_code="2002",
                account_name="Trade Creditors",
                closing_cr_paise=30000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=5,
                account_code="3001",
                account_name="Sales Revenue",
                closing_cr_paise=300000000,
            ),
            # Assets & Expenses
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=6,
                account_code="4001",
                account_name="Plant Machinery",
                closing_dr_paise=100000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=7,
                account_code="4002",
                account_name="Closing Stock",
                closing_dr_paise=40000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=8,
                account_code="4003",
                account_name="Sundry Debtors",
                closing_dr_paise=35000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=9,
                account_code="4004",
                account_name="Bank Balance",
                closing_dr_paise=35000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=10,
                account_code="5001",
                account_name="Direct Costs",
                closing_dr_paise=180000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=11,
                account_code="5002",
                account_name="Salaries",
                closing_dr_paise=80000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=12,
                account_code="5003",
                account_name="Finance Interest",
                closing_dr_paise=5000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=13,
                account_code="5004",
                account_name="Depreciation",
                closing_dr_paise=35000000,
            ),
        ]
        fin_repo.add_trial_balance_lines(tb_lines)

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
        map_service.update_mapping(eng.id, code, cat, line, lead, atype, "Mapping")

    return {"db_manager": db_manager, "engagement_id": eng.id, "user_id": user.id}


def test_cash_flow_indirect_method_and_reconciliation(test_setup) -> None:
    """Verify Cash Flow statement generates operating, investing, and financing flows and reconciles with Balance Sheet cash."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="senior_user", role=RoleEnum.SENIOR)
    )

    fs_service = FinancialStatementService(db_manager)
    dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)

    cf = fs_service.generate_cash_flow_statement(dto)
    assert cf is not None
    assert len(cf.operating_activities) > 0
    assert len(cf.investing_activities) > 0
    assert len(cf.financing_activities) > 0

    # Invariants
    assert cf.financial_statement_cash_balance_paise == 35000000  # ₹3,50,000 in paise
    assert cf.closing_cash_and_equivalents_paise == 35000000
    assert cf.is_reconciled is True
    assert cf.reconciliation_difference_paise == 0


def test_cash_flow_discrepancy_detection(test_setup) -> None:
    """Verify that any intentional imbalance in Cash Flow calculation triggers is_reconciled = False."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="senior_user", role=RoleEnum.SENIOR)
    )

    fs_service = FinancialStatementService(db_manager)
    dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)

    bs = fs_service.generate_balance_sheet(dto)
    pnl = fs_service.generate_profit_and_loss(dto)

    # Intentionally corrupt BS cash balance to test failure detection
    for l in bs.assets_lines:
        if l.category == "Cash and Cash Equivalents":
            l.current_period_paise = 999999999

    from finauditpro.domain.cash_flow_evaluation_engine import (
        build_indirect_cash_flow_statement,
    )

    corrupted_cf = build_indirect_cash_flow_statement(eng_id, "2025-26", bs, pnl)
    assert corrupted_cf.is_reconciled is False
    assert corrupted_cf.reconciliation_difference_paise != 0
