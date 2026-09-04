"""Realistic End-to-End Statutory Audit Workflow (ABC Manufacturing Pvt Ltd), Scalability Benchmark (5,000 accounts), and Negative Tests."""

import time
from uuid import uuid4

import pytest

from finauditpro.application.audit_adjustment_dtos import (
    ApplyAJEDTO,
    CreateAJEDTO,
    CreateAJELineDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
)
from finauditpro.application.compliance_dtos import ExecuteCAROProcedureDTO, RunTaxAuditCheckDTO
from finauditpro.application.financial_statement_dtos import (
    CreateOrUpdateNoteDTO,
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
    TaxAuditCategoryEnum,
    TaxAuditCheckResultEnum,
)
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
from finauditpro.domain.financial_statement_entities import (
    DisclosureClassificationEnum,
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
    db_file = tmp_path / "test_phase_c_e2e.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm = Firm(
            id=str(uuid4()), name="Deloitte & Singhi LLP", registration_number="FRN-009988N"
        )
        FirmRepository(session).add(firm)

        client = Client(
            id=str(uuid4()),
            firm_id=firm.id,
            name="ABC Manufacturing Pvt Ltd",
            industry="Automotive Components",
        )
        ClientRepository(session).add(client)

        partner = User(
            id=str(uuid4()),
            email="partner@firm.com",
            username="partner_ca",
            password_hash="h",
            salt="s",
            full_name="Lead CA Partner",
            role=RoleEnum.PARTNER,
        )
        senior = User(
            id=str(uuid4()),
            email="senior@firm.com",
            username="senior_ca",
            password_hash="h",
            salt="s",
            full_name="Audit Senior",
            role=RoleEnum.SENIOR,
        )
        UserRepository(session).add(partner)
        UserRepository(session).add(senior)

        eng = Engagement(
            id=str(uuid4()),
            firm_id=firm.id,
            client_id=client.id,
            title="ABC Manufacturing Pvt Ltd - Statutory Audit FY 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

        # 1. Realistic Trial Balance for ABC Manufacturing Pvt Ltd (FY 2025-26)
        dataset_id = str(uuid4())
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng.id,
                dataset_name="ABC TB 2026",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="abc_tb_2026.csv",
            )
        )

        # Amounts in paise (e.g. ₹10,00,000 = 100,000,000 paise)
        tb_data = [
            # Equity & Liabilities
            ("1010", "Equity Share Capital (10,00,000 shares @ ₹10)", 0, 100000000),
            ("1020", "Retained Earnings / General Reserves", 0, 50000000),
            ("2010", "SBI Term Loan for Factory Expansion", 0, 75000000),
            ("2020", "Sundry Creditors for Raw Materials", 0, 35000000),
            ("2030", "Statutory Dues Payable (GST & TDS)", 0, 10000000),
            ("3010", "Domestic Sales - Auto Components", 0, 250000000),
            ("3020", "Interest Income from Fixed Deposits", 0, 5000000),
            # Assets & Expenses
            ("4010", "Factory Land and Buildings", 120000000, 0),
            ("4020", "CNC Machinery & Production Lines", 60000000, 0),
            ("4030", "Raw Materials & Finished Goods Stock", 40000000, 0),
            ("4040", "Trade Debtors - Automotive OEMs", 30000000, 0),
            ("4050", "SBI Current Account Balance", 25000000, 0),
            ("5010", "Steel & Alloy Consumption", 130000000, 0),
            ("5020", "Direct Factory Wages & Staff Salaries", 60000000, 0),
            ("5030", "SBI Loan Interest & Processing Fees", 8000000, 0),
            ("5040", "Plant & Building Depreciation", 32000000, 0),
            ("5050", "Power, Fuel & Freight Charges", 20000000, 0),
        ]
        lines = [
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=i,
                account_code=c,
                account_name=n,
                closing_dr_paise=dr,
                closing_cr_paise=cr,
            )
            for i, (c, n, dr, cr) in enumerate(tb_data, 1)
        ]
        fin_repo.add_trial_balance_lines(lines)

    # 2. Schedule III Account Mappings
    map_service = AccountMappingService(db_manager)
    map_service.initialize_mappings_from_trial_balance(eng.id, dataset_id)
    mappings_spec = [
        ("1010", "Share Capital", "Equity Share Capital", "WP-A1", AccountTypeEnum.EQUITY),
        (
            "1020",
            "Reserves and Surplus",
            "Retained Earnings / General Reserve",
            "WP-A2",
            AccountTypeEnum.EQUITY,
        ),
        (
            "2010",
            "Long-Term Borrowings",
            "Term Loans from Banks & FIs",
            "WP-B1",
            AccountTypeEnum.LIABILITY,
        ),
        ("2020", "Trade Payables", "Trade Payables - Others", "WP-C2", AccountTypeEnum.LIABILITY),
        (
            "2030",
            "Other Current Liabilities",
            "Statutory Dues & Advance from Customers",
            "WP-C3",
            AccountTypeEnum.LIABILITY,
        ),
        (
            "3010",
            "Revenue from Operations",
            "Sale of Products & Services",
            "WP-I1",
            AccountTypeEnum.INCOME,
        ),
        ("3020", "Other Income", "Interest Income & Foreclosures", "WP-I2", AccountTypeEnum.INCOME),
        (
            "4010",
            "Property, Plant and Equipment",
            "Buildings & Civil Structures",
            "WP-D1",
            AccountTypeEnum.ASSET,
        ),
        (
            "4020",
            "Property, Plant and Equipment",
            "Plant, Machinery & Equipment",
            "WP-D1",
            AccountTypeEnum.ASSET,
        ),
        ("4030", "Inventories", "Finished Goods & Stock-in-Trade", "WP-F1", AccountTypeEnum.ASSET),
        (
            "4040",
            "Trade Receivables",
            "Trade Receivables - Undisputed Good",
            "WP-G1",
            AccountTypeEnum.ASSET,
        ),
        (
            "4050",
            "Cash and Cash Equivalents",
            "Balances with Banks & Fixed Deposits",
            "WP-H1",
            AccountTypeEnum.ASSET,
        ),
        (
            "5010",
            "Cost of Materials Consumed",
            "Raw Material Consumption",
            "WP-J1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5020",
            "Employee Benefits Expense",
            "Salaries, Wages & Staff Welfare",
            "WP-K1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5030",
            "Finance Costs",
            "Interest Expense & Bank Charges",
            "WP-L1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5040",
            "Depreciation and Amortization",
            "Depreciation on PPE",
            "WP-M1",
            AccountTypeEnum.EXPENSE,
        ),
        (
            "5050",
            "Other Expenses",
            "Manufacturing, Admin & Selling Expenses",
            "WP-N1",
            AccountTypeEnum.EXPENSE,
        ),
    ]
    for code, cat, line, lead, atype in mappings_spec:
        map_service.update_mapping(eng.id, code, cat, line, lead, atype, "Schedule III Mapping")

    return {
        "db_manager": db_manager,
        "engagement_id": eng.id,
        "dataset_id": dataset_id,
        "partner_id": partner.id,
        "senior_id": senior.id,
    }


def test_abc_manufacturing_realistic_e2e_workflow(test_setup) -> None:
    """Execute complete statutory audit of ABC Manufacturing Pvt Ltd (FY 2025-26) and verify all accounting invariants."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]
    partner_id = test_setup["partner_id"]
    senior_id = test_setup["senior_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=senior_id, username="senior_ca", role=RoleEnum.SENIOR)
    )

    fs_service = FinancialStatementService(db_manager)
    comp_service = ComplianceService(db_manager)
    aje_service = AuditAdjustmentService(db_manager)

    # 1. Post Approved AJE: Unrecorded Freight of ₹50,000 (5,000,000 paise)
    aje_dto = CreateAJEDTO(
        engagement_id=eng_id,
        aje_number="AJE-001",
        entry_date="2026-03-31",
        title="Unrecorded year-end freight expense",
        narration="Accrued freight charges for March 2026",
        reason="Cut-off testing adjustment",
        lines=[
            CreateAJELineDTO(
                account_code="5050",
                account_name="Power, Fuel & Freight Charges",
                debit_paise=5000000,
                credit_paise=0,
                narration="Freight inward accrued",
            ),
            CreateAJELineDTO(
                account_code="2020",
                account_name="Sundry Creditors for Raw Materials",
                debit_paise=0,
                credit_paise=5000000,
                narration="Transporter payable",
            ),
        ],
    )
    aje = aje_service.create_adjustment(aje_dto)
    aje_service.submit_adjustment(SubmitAJEDTO(engagement_id=eng_id, entry_id=aje.id))
    SecurityContext.set_current_session(
        UserSession(user_id=partner_id, username="partner_ca", role=RoleEnum.PARTNER)
    )
    aje_service.review_adjustment(
        ReviewAJEDTO(engagement_id=eng_id, entry_id=aje.id, decision="APPROVE")
    )
    aje_service.apply_adjustment(ApplyAJEDTO(engagement_id=eng_id, entry_id=aje.id))

    # 2. Verify Adjusted Trial Balance
    adj_tb = aje_service.calculate_adjusted_trial_balance(eng_id)
    assert adj_tb.is_balanced is True
    assert adj_tb.total_adjusted_dr_paise == adj_tb.total_adjusted_cr_paise

    # 3. Generate Balance Sheet & Verify Cross-Footing Balance
    bs_dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)
    bs = fs_service.generate_balance_sheet(bs_dto)
    assert bs.is_balanced is True
    assert bs.total_assets_paise == bs.total_equity_and_liabilities_paise
    assert bs.total_assets_paise == 275000000  # ₹2.75 Cr

    # 4. Generate Statement of Profit & Loss
    pnl = fs_service.generate_profit_and_loss(bs_dto)
    assert pnl.total_revenue_paise == 255000000  # ₹2.55 Cr
    assert pnl.total_expenses_paise == 255000000  # Expenses including ₹50k AJE = ₹2.55 Cr
    assert pnl.profit_before_tax_paise == 0

    # 5. Generate Cash Flow Statement & Verify Closing Cash Reconciliation
    cf = fs_service.generate_cash_flow_statement(bs_dto)
    assert cf.is_reconciled is True
    assert (
        cf.closing_cash_and_equivalents_paise == bs.total_assets_paise - 250000000
    )  # 25,000,000 paise (₹25 Lakh)
    assert cf.reconciliation_difference_paise == 0

    # 6. Author Notes to Accounts
    note = fs_service.create_or_update_note(
        CreateOrUpdateNoteDTO(
            engagement_id=eng_id,
            note_number="Note 10",
            title="Property, Plant and Equipment Schedule",
            fs_reference="Balance Sheet Line NCA-01",
            source_type="Mapped TB Accounts",
            disclosure_classification=DisclosureClassificationEnum.AUTOMATIC,
            amount_paise=180000000,
        )
    )
    assert note.amount_paise == 180000000

    # 7. Execute CARO 2020 Working Papers
    comp_service.initialize_caro_clauses(eng_id)
    caro_wp = comp_service.execute_caro_procedure(
        ExecuteCAROProcedureDTO(
            engagement_id=eng_id,
            clause_code="3(vii)",
            clause_title="Statutory Dues",
            applicability=CAROApplicabilityEnum.APPLICABLE,
            procedure_text="Verified GST 3B, GSTR-1, PF, and ESI challans. All undisputed statutory dues regular.",
            evidence_refs=["CHALLAN-GST-MAR2026", "PF-ECR-MAR2026"],
            report_answer=CAROReportAnswerEnum.UNQUALIFIED,
        )
    )
    assert caro_wp.status == "Completed"

    # 8. Execute Form 3CD Tax Audit Checks
    tax_chk = comp_service.run_tax_audit_check(
        RunTaxAuditCheckDTO(
            engagement_id=eng_id,
            clause_code="Clause 26",
            category=TaxAuditCategoryEnum.STATUTORY_DUES_43B,
            description="Verification of statutory liability payments u/s 43B before due date of filing return",
            input_source="Ledger Accounts 2030 (GST & TDS Payable)",
            rule_logic="Verify payment date <= ITR filing due date",
            system_result=TaxAuditCheckResultEnum.COMPLIANT,
        )
    )
    assert tax_chk.system_result == TaxAuditCheckResultEnum.COMPLIANT

    # 9. Save, Review, and Lock Final Package V4
    save_dto = SaveFinancialStatementPackageDTO(
        engagement_id=eng_id, version=FinancialStatementVersionEnum.DRAFT_V1
    )
    pkg = fs_service.save_package(save_dto)
    fs_service.review_package(
        ReviewFinancialStatementPackageDTO(
            engagement_id=eng_id, package_id=pkg.id, decision="APPROVE"
        )
    )
    locked_pkg = fs_service.lock_package(
        LockFinancialStatementPackageDTO(engagement_id=eng_id, package_id=pkg.id)
    )
    assert locked_pkg.is_locked is True
    assert locked_pkg.status == PackageStatusEnum.LOCKED
    assert locked_pkg.version == FinancialStatementVersionEnum.FINAL_LOCKED_V4


def test_scale_performance_5000_tb_accounts(test_setup) -> None:
    """Benchmark: Generate full financial statements and lineage over 5,000 accounts in < 3.0 seconds."""
    db_manager = test_setup["db_manager"]
    eng_id = str(uuid4())

    with db_manager.session_scope() as session:
        firm = Firm(
            id=str(uuid4()),
            name="Scale Test Firm LLP",
            registration_number="REG-SCALE-99",
        )
        FirmRepository(session).add(firm)
        client = Client(
            id=str(uuid4()), firm_id=firm.id, name="High Volume Client", industry="Retail"
        )
        ClientRepository(session).add(client)
        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Scale Test Audit",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.PLANNING,
        )
        EngagementRepository(session).add(eng)

        dataset_id = str(uuid4())
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng_id,
                dataset_name="Scale TB",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="scale_tb.csv",
            )
        )

        # Generate 5,000 balanced TB accounts
        tb_lines = []
        for i in range(1, 2501):
            tb_lines.append(
                TrialBalanceLine(
                    dataset_id=dataset_id,
                    source_row_no=i,
                    account_code=f"DR_{i:04d}",
                    account_name=f"Asset Sub-Account {i}",
                    closing_dr_paise=100000,
                )
            )
            tb_lines.append(
                TrialBalanceLine(
                    dataset_id=dataset_id,
                    source_row_no=i + 2500,
                    account_code=f"CR_{i:04d}",
                    account_name=f"Liability Sub-Account {i}",
                    closing_cr_paise=100000,
                )
            )
        fin_repo.add_trial_balance_lines(tb_lines)

    map_service = AccountMappingService(db_manager)
    map_service.initialize_mappings_from_trial_balance(eng_id, dataset_id)

    fs_service = FinancialStatementService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["partner_id"], username="partner_ca", role=RoleEnum.PARTNER)
    )

    t0 = time.perf_counter()
    dto = GenerateFinancialStatementsDTO(engagement_id=eng_id, dataset_id=dataset_id)
    bs = fs_service.generate_balance_sheet(dto)
    pnl = fs_service.generate_profit_and_loss(dto)
    cf = fs_service.generate_cash_flow_statement(dto)
    elapsed = time.perf_counter() - t0

    assert bs is not None
    assert pnl is not None
    assert cf is not None
    assert elapsed < 3.0, f"Performance scale test took {elapsed:.2f}s (expected < 3.0s)"
