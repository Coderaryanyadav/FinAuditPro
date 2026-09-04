"""End-to-End test for Phase D: Comprehensive Audit Completion Workflow on Realistic Indian Manufacturing Audit."""

from uuid import uuid4

from finauditpro.application.audit_completion_dtos import (
    CreateGoingConcernAssessmentDTO,
    CreateSubsequentEventDTO,
)
from finauditpro.application.financial_statement_dtos import (
    GenerateFinancialStatementsDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_completion_entities import (
    GoingConcernConclusionEnum,
    SA450AuditConclusionEnum,
    SolvencyRiskLevelEnum,
)
from finauditpro.domain.audit_execution_entities import AuditMisstatement
from finauditpro.domain.audit_matrix_entities import MaterialityAssessment
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
    AuditMatrixRepository,
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
)
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)


def test_phase_d_comprehensive_audit_completion_workflow(tmp_path: any) -> None:
    db_path = tmp_path / "test_phase_d_e2e.db"
    db_manager = initialize_database(db_path)

    eng_id = "eng-abc-mfg-completion"

    # Step 1: Set up Users, Engagement, and TB
    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="partner_ak",
                password_hash="h",
                salt="s",
                display_name="CA Ananya Kapoor (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        senior = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="senior_ca",
                password_hash="h",
                salt="s",
                display_name="CA Rahul Mehta (Senior)",
                role=RoleEnum.SENIOR,
            )
        )

        firm = Firm(id="firm-abc", name="ABC Audit LLP")
        FirmRepository(session).add(firm)

        client = Client(
            id="client-abc",
            firm_id=firm.id,
            name="ABC Manufacturing Pvt Ltd",
            pan_number="AABCA1234F",
            cin_number="U29100MH2015PTC123456",
        )
        ClientRepository(session).add(client)

        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit FY 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

        fin_repo = FinancialDataRepository(session)
        dataset_id = str(uuid4())
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng.id,
                dataset_name="ABC TB 2026",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="abc_tb_2026.csv",
            )
        )

        tb_data = [
            ("1010", "Equity Share Capital", 0, 100000000),
            ("1020", "Retained Earnings / General Reserves", 0, 50000000),
            ("2010", "SBI Term Loan for Factory Expansion", 0, 75000000),
            ("2020", "Sundry Creditors for Raw Materials", 0, 35000000),
            ("2030", "Statutory Dues Payable (GST & TDS)", 0, 15000000),
            ("3010", "Domestic Sales - Auto Components", 0, 250000000),
            ("3020", "Interest Income from Fixed Deposits", 0, 5000000),
            ("4010", "Factory Land and Buildings", 120000000, 0),
            ("4020", "CNC Machinery & Production Lines", 60000000, 0),
            ("4030", "Raw Materials & Finished Goods Stock", 40000000, 0),
            ("4040", "Trade Debtors - Automotive OEMs", 30000000, 0),
            ("4050", "SBI Current Account Balance", 25000000, 0),
            ("5010", "Steel & Alloy Consumption", 130000000, 0),
            ("5020", "Direct Factory Wages & Staff Salaries", 60000000, 0),
            ("5030", "SBI Loan Interest & Processing Fees", 8000000, 0),
            ("5040", "Plant & Building Depreciation", 32000000, 0),
            ("5050", "Power, Fuel & Freight Charges", 25000000, 0),
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

        # Materiality under SA 320
        mat_repo = AuditMatrixRepository(session)
        mat = MaterialityAssessment(
            engagement_id=eng_id,
            benchmark_name="Profit Before Tax",
            benchmark_value_paise=1000000000,  # ₹10 Crore
            benchmark_percentage=5.0,
            overall_materiality_paise=50000000,  # ₹50 Lakhs
            performance_materiality_paise=37500000,  # ₹37.5 Lakhs
            clearly_trivial_threshold_paise=2500000,  # ₹2.5 Lakhs
            rationale="Standard 5% of PBT for commercial manufacturing entity",
        )
        mat_repo.add_materiality(mat)

        # Misstatement under SA 450
        core_repo = CoreAuditEngineRepository(session)
        misst = AuditMisstatement(
            engagement_id=eng_id,
            account_code="2020",
            account_name="Sundry Creditors for Raw Materials",
            schedule_iii_category="Trade Payables",
            amount_paise=15000000,  # ₹15 Lakhs (Uncorrected, below OM ₹50L)
            rationale="Unrecorded vendor invoice received in April relating to March services",
            created_by="Senior Auditor",
        )
        core_repo.add_misstatement(misst)

    # Step 2: Initialize Mappings & Generate Financial Statements Package
    SecurityContext.set_current_session(
        UserSession(user_id=senior.id, username="senior_ca", role=RoleEnum.SENIOR)
    )
    map_service = AccountMappingService(db_manager)
    map_service.initialize_mappings_from_trial_balance(eng_id, dataset_id)
    mappings_spec = [
        ("1010", "Share Capital", "Equity Share Capital", "WP-A1", AccountTypeEnum.EQUITY),
        ("1020", "Reserves and Surplus", "Retained Earnings", "WP-A2", AccountTypeEnum.EQUITY),
        ("2010", "Long-Term Borrowings", "Term Loans", "WP-B1", AccountTypeEnum.LIABILITY),
        ("2020", "Trade Payables", "Sundry Creditors", "WP-C1", AccountTypeEnum.LIABILITY),
        ("2030", "Other Current Liabilities", "Statutory Dues", "WP-C2", AccountTypeEnum.LIABILITY),
        ("3010", "Revenue from Operations", "Domestic Sales", "WP-D1", AccountTypeEnum.REVENUE),
        ("3020", "Other Income", "Interest Income", "WP-D2", AccountTypeEnum.REVENUE),
        ("4010", "Property, Plant and Equipment", "Land & Buildings", "WP-E1", AccountTypeEnum.ASSET),
        ("4020", "Property, Plant and Equipment", "Machinery", "WP-E2", AccountTypeEnum.ASSET),
        ("4030", "Inventories", "Stock", "WP-F1", AccountTypeEnum.ASSET),
        ("4040", "Trade Receivables", "Trade Debtors", "WP-G1", AccountTypeEnum.ASSET),
        ("4050", "Cash and Cash Equivalents", "Bank Balances", "WP-H1", AccountTypeEnum.ASSET),
        ("5010", "Cost of Materials Consumed", "Steel Consumption", "WP-J1", AccountTypeEnum.EXPENSE),
        ("5020", "Employee Benefits Expense", "Salaries & Wages", "WP-K1", AccountTypeEnum.EXPENSE),
        ("5030", "Finance Costs", "Loan Interest", "WP-L1", AccountTypeEnum.EXPENSE),
        ("5040", "Depreciation and Amortization Expense", "Depreciation", "WP-M1", AccountTypeEnum.EXPENSE),
        ("5050", "Other Expenses", "Power & Freight", "WP-N1", AccountTypeEnum.EXPENSE),
    ]
    for code, cat, subcat, wp, atype in mappings_spec:
        map_service.update_mapping(eng_id, code, cat, subcat, wp, atype)

    fs_service = FinancialStatementService(db_manager)
    bs_dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)
    bs = fs_service.generate_balance_sheet(bs_dto)
    pnl = fs_service.generate_profit_and_loss(bs_dto)
    cf = fs_service.generate_cash_flow_statement(bs_dto)

    save_dto = SaveFinancialStatementPackageDTO(
        engagement_id=eng_id,
        balance_sheet=bs,
        profit_loss=pnl,
        cash_flow=cf,
    )
    fs_service.save_package(save_dto)

    # Step 3: Execute Phase D Audit Completion Workflows
    completion_service = AuditCompletionService(db_manager)

    # 1. SA 450 Misstatement Evaluation
    sa450_summary = completion_service.evaluate_sa450_misstatements(eng_id)
    assert sa450_summary.total_identified_misstatements == 1
    assert sa450_summary.total_uncorrected_misstatements == 1
    assert not sa450_summary.requires_opinion_modification
    assert sa450_summary.audit_conclusion == SA450AuditConclusionEnum.UNQUALIFIED_ACCEPTABLE.value

    # 2. SA 570 Going Concern Assessment & Partner Sign-off
    SecurityContext.set_current_session(
        UserSession(user_id=partner.id, username="partner_ak", role=RoleEnum.PARTNER)
    )
    gc_dto = CreateGoingConcernAssessmentDTO(
        has_operating_losses=False,
        has_negative_operating_cashflow=False,
        has_negative_net_worth=False,
        current_ratio=2.33,
        debt_equity_ratio=0.50,
        mitigations=[],
        partner_signoff=True,
        reviewer="CA Ananya Kapoor",
    )
    gc_res = completion_service.create_or_update_going_concern_assessment(eng_id, gc_dto)
    assert gc_res.solvency_risk_level == SolvencyRiskLevelEnum.LOW.value
    assert gc_res.audit_conclusion == GoingConcernConclusionEnum.NO_MATERIAL_UNCERTAINTY.value
    assert gc_res.partner_signoff is True

    # 3. SA 580 Management Representation Letter Generation & Signature
    mrl_dto = completion_service.generate_default_mrl(
        engagement_id=eng_id,
        financial_year="2025-26",
        requested_date="2026-08-15",
    )
    assert len(mrl_dto.clauses) == 6

    mrl_signed = completion_service.update_mrl_status(
        engagement_id=eng_id,
        mrl_id=mrl_dto.id,
        status="Signed by Management",
        signed_date="2026-08-25",
        signatory_name="Anand Singhal",
        signatory_designation="Managing Director",
        audit_report_date="2026-08-26",
    )
    assert mrl_signed.is_chronologically_valid is True

    # 4. SA 560 Subsequent Events Register
    event_dto = CreateSubsequentEventDTO(
        event_date="2026-05-10",
        event_type="Non-Adjusting Event (Condition arose Subsequent to Balance Sheet Date)",
        description="Acquisition of new manufacturing plant in Pune for ₹10 Crore announced",
        estimated_amount_paise=1000000000,
        accounting_treatment="Disclosed in Notes to Accounts (AS 4 / Ind AS 10)",
        is_adjusted_in_fs=False,
        is_disclosed_in_notes=True,
        procedure_applied="Review of subsequent board minutes and press releases",
        auditor_conclusion="Properly disclosed in Note 24 of Financial Statements.",
    )
    subseq_res = completion_service.record_subsequent_event(eng_id, event_dto)
    assert subseq_res.is_disclosed_in_notes is True

    # 5. SA 520 Final Analytical Review
    far_res = completion_service.perform_final_analytical_review(engagement_id=eng_id)
    assert len(far_res.ratio_lines) >= 3
    assert "conformance" in far_res.overall_consistency_conclusion.lower() or "relationships" in far_res.overall_consistency_conclusion.lower()
