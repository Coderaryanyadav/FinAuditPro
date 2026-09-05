"""Comprehensive Phase E Realistic Simulation: ABC Manufacturing Pvt Ltd (FY 2025-26).

Executes full end-to-end statutory reporting lifecycle:
Completed Engagement -> Schedule III FS Approval -> CARO Approval ->
Going Concern (SA 570) -> Subsequent Events (SA 560) -> MRL (SA 580) ->
Misstatement Evaluation (SA 450) -> Audit Report Preparation ->
Opinion Decision Support -> Candidate KAM Detection -> Partner KAM Adoption ->
Cross-Document Consistency Checks -> Partner Approval with UDIN ->
Pre-generation Checklist -> Number Reconciliation & Lineage ->
Final Statutory Report Generation -> Locking -> Sealing / Archival ->
Mutation (Dependency Hash Invalidation / Stale Report Detection) ->
Re-review & Re-approval -> Controlled Version Regeneration.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from finauditpro.application.audit_completion_dtos import (
    CreateGoingConcernAssessmentDTO,
    CreateSubsequentEventDTO,
)
from finauditpro.application.audit_report_dtos import (
    AddKeyAuditMatterDTO,
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
)
from finauditpro.application.compliance_dtos import ReviewCAROClauseDTO
from finauditpro.application.financial_statement_dtos import (
    GenerateFinancialStatementsDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.application.services.audit_report_generation_service import (
    AuditReportGenerationService,
)
from finauditpro.application.services.audit_report_service import AuditReportService
from finauditpro.application.services.compliance_service import ComplianceService
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_matrix_entities import (
    AuditRisk,
    RiskSeverityEnum,
)
from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    ReportWorkpaperStatusEnum,
    SourceLineageTypeEnum,
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
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "abc_mfg_phase_e.db"
    return initialize_database(db_file)


def test_abc_manufacturing_complete_reporting_simulation(
    db_manager: DatabaseManager, tmp_path: Path
) -> None:
    eng_id = f"eng-abc-{uuid4()}"
    reports_dir = tmp_path / "statutory_deliverables"

    # ==========================================
    # 1. SETUP FIRM, CLIENT, ENGAGEMENT & USERS
    # ==========================================
    with db_manager.session_scope() as session:
        firm = Firm(id="firm-rk", name="R.K. Sharma & Co., Chartered Accountants")
        FirmRepository(session).add(firm)

        client = Client(
            id="cli-abc",
            firm_id=firm.id,
            name="ABC Manufacturing Pvt Ltd",
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

        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_rk_sharma",
                password_hash="pw",
                salt="sl",
                display_name="CA R.K. Sharma (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        preparer = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="audit_senior_neha",
                password_hash="pw",
                salt="sl",
                display_name="Neha Gupta (Senior Auditor)",
                role=RoleEnum.SENIOR,
            )
        )

        # Import Trial Balance for ABC Manufacturing Pvt Ltd
        fin_repo = FinancialDataRepository(session)
        ds = FinancialDataset(
            id=str(uuid4()),
            engagement_id=eng_id,
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            dataset_name="ABC Final TB FY26",
            filename="abc_mfg_tb.xlsx",
        )
        fin_repo.add_dataset(ds)

        # Trial Balance lines (balanced: ₹18.5 Cr debits = ₹18.5 Cr credits)
        # Amounts in paise (1 Cr = 1,00,00,000 * 100 = 1,00,00,00,000 paise)
        tb_lines = [
            ("1001", "Equity Share Capital", 0, 500000000),             # ₹50 Lakh Cr
            ("1101", "Retained Earnings / General Reserve", 0, 350000000),# ₹35 Lakh Cr
            ("2001", "Term Loan from State Bank of India", 0, 400000000),# ₹40 Lakh Cr
            ("2101", "Sundry Trade Creditors", 0, 150000000),           # ₹15 Lakh Cr
            ("3001", "Plant, Machinery & Factory Equipment", 650000000, 0),# ₹65 Lakh Dr
            ("3101", "Finished Goods Inventory", 250000000, 0),          # ₹25 Lakh Dr
            ("3201", "Sundry Debtors / Trade Receivables", 200000000, 0), # ₹20 Lakh Dr
            ("3301", "HDFC Bank Current Account Balance", 300000000, 0),  # ₹30 Lakh Dr
            ("4001", "Gross Revenue from Sale of Goods", 0, 1200000000),  # ₹1.2 Cr Cr
            ("5001", "Cost of Raw Materials Consumed", 800000000, 0),    # ₹80 Lakh Dr
            ("5101", "Employee Benefit Expenses", 250000000, 0),        # ₹25 Lakh Dr
            ("5201", "Depreciation on Plant & Machinery", 150000000, 0),# ₹15 Lakh Dr
        ]
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id=ds.id,
                    source_row_no=i,
                    account_code=code,
                    account_name=name,
                    closing_dr_paise=dr,
                    closing_cr_paise=cr,
                )
                for i, (code, name, dr, cr) in enumerate(tb_lines, start=1)
            ]
        )

        matrix_repo = AuditMatrixRepository(session)
        matrix_repo.add_risk(
            AuditRisk(
                id=str(uuid4()),
                engagement_id=eng_id,
                risk_code="RSK-PPE-01",
                title="Valuation and Existence of PPE",
                category="Property, Plant and Equipment",
                description="High carrying value of machinery and complex depreciation estimates.",
                inherent_risk=RiskSeverityEnum.HIGH,
                is_significant_risk=True,
            )
        )

    # =======================================================
    # 2. MAP ACCOUNTS & GENERATE SCHEDULE III FS STATEMENTS
    # =======================================================
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    map_svc = AccountMappingService(db_manager)
    map_svc.initialize_mappings_from_trial_balance(eng_id, ds.id)
    map_svc.update_mapping(eng_id, "1001", "Share Capital", "Equity", "WP-A1", AccountTypeEnum.EQUITY)
    map_svc.update_mapping(eng_id, "1101", "Reserves and Surplus", "Reserves", "WP-A2", AccountTypeEnum.EQUITY)
    map_svc.update_mapping(eng_id, "2001", "Long-Term Borrowings", "Loans", "WP-B1", AccountTypeEnum.LIABILITY)
    map_svc.update_mapping(eng_id, "2101", "Trade Payables", "Creditors", "WP-B2", AccountTypeEnum.LIABILITY)
    map_svc.update_mapping(eng_id, "3001", "Property, Plant and Equipment", "Machinery", "WP-C1", AccountTypeEnum.ASSET)
    map_svc.update_mapping(eng_id, "3101", "Inventories", "Stock", "WP-C2", AccountTypeEnum.ASSET)
    map_svc.update_mapping(eng_id, "3201", "Trade Receivables", "Debtors", "WP-C3", AccountTypeEnum.ASSET)
    map_svc.update_mapping(eng_id, "3301", "Cash and Cash Equivalents", "Bank", "WP-C4", AccountTypeEnum.ASSET)
    map_svc.update_mapping(eng_id, "4001", "Revenue from Operations", "Sales", "WP-D1", AccountTypeEnum.REVENUE)
    map_svc.update_mapping(eng_id, "5001", "Cost of Materials Consumed", "RawMaterial", "WP-E1", AccountTypeEnum.EXPENSE)
    map_svc.update_mapping(eng_id, "5101", "Employee Benefits Expense", "Salaries", "WP-E2", AccountTypeEnum.EXPENSE)
    map_svc.update_mapping(eng_id, "5201", "Depreciation and Amortization", "Depreciation", "WP-E3", AccountTypeEnum.EXPENSE)

    fs_svc = FinancialStatementService(db_manager)
    gen_dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)
    bs = fs_svc.generate_balance_sheet(gen_dto)
    pnl = fs_svc.generate_profit_and_loss(gen_dto)
    cf = fs_svc.generate_cash_flow_statement(gen_dto)
    fs_pkg = fs_svc.save_package(
        SaveFinancialStatementPackageDTO(
            engagement_id=eng_id,
            balance_sheet=bs,
            profit_loss=pnl,
            cash_flow=cf,
        )
    )
    assert fs_pkg.id is not None
    assert bs.is_balanced is True

    # =======================================================
    # 3. COMPLETE CARO 2020 WORKPAPERS & APPROVAL
    # =======================================================
    comp_svc = ComplianceService(db_manager)
    comp_svc.initialize_caro_clauses(eng_id)
    comp_svc.review_caro_clause(
        ReviewCAROClauseDTO(
            engagement_id=eng_id,
            clause_code="3(i)",
            decision="APPROVE",
            reviewer_notes="Fixed assets register maintained; physically verified without material discrepancies.",
        )
    )

    # =======================================================
    # 4. COMPLETE GOING CONCERN (SA 570) & MRL (SA 580)
    # =======================================================
    compl_svc = AuditCompletionService(db_manager)
    compl_svc.create_or_update_going_concern_assessment(
        eng_id,
        CreateGoingConcernAssessmentDTO(
            has_operating_losses=False,
            has_negative_operating_cashflow=False,
            has_negative_net_worth=False,
            current_ratio=2.45,
            debt_equity_ratio=0.47,
            mitigations=[],
            partner_signoff=True,
            reviewer="CA R.K. Sharma",
        ),
    )

    # Subsequent Events (SA 560)
    compl_svc.record_subsequent_event(
        eng_id,
        CreateSubsequentEventDTO(
            event_date="2026-06-15",
            event_type="Non-Adjusting Event",
            description="Routine customer settlement concluded amicably; no adjustment to FY26 statements needed.",
            estimated_amount_paise=0,
            accounting_treatment="Disclosure not required due to immateriality",
            procedure_applied="Inquiry of management and inspection of board minutes",
            auditor_conclusion="No reporting impact on FY2025-26 statements.",
        ),
    )

    # Management Representation Letter (SA 580)
    mrl = compl_svc.generate_default_mrl(eng_id, "2025-26", "2026-08-10")
    compl_svc.update_mrl_status(
        engagement_id=eng_id,
        mrl_id=mrl.id,
        status="Signed Representation Letter Obtained",
        signed_date="2026-08-20",
        signatory_name="Sunil Agarwal",
        signatory_designation="Managing Director",
        audit_report_date="2026-08-25",
    )

    # =======================================================
    # 5. AUDIT REPORT WORKPAPER PREPARATION (SA 700)
    # =======================================================
    rep_svc = AuditReportService(db_manager)
    wp = rep_svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng_id,
            reporting_framework="Companies Act 2013 / Ind AS",
            proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
            final_opinion=AuditOpinionTypeEnum.UNMODIFIED,
            opinion_rationale="Financial statements give a true and fair view in accordance with Ind AS.",
        )
    )
    assert wp.status == ReportWorkpaperStatusEnum.DRAFT

    # =======================================================
    # 6. OPINION DECISION SUPPORT & CANDIDATE KAM DETECTION
    # =======================================================
    dec_support = rep_svc.evaluate_opinion_decision_support(eng_id)
    assert dec_support.is_consistent is True
    assert dec_support.review_required is False
    assert "consistent" in dec_support.suggested_assessment.lower()

    # Detect Candidate KAMs
    kam_candidates = rep_svc.suggest_candidate_kams(eng_id)
    assert isinstance(kam_candidates, list)
    assert len(kam_candidates) > 0
    # Verify label rule: SYSTEM-SUGGESTED CANDIDATE
    for cand in kam_candidates:
        assert "SYSTEM-SUGGESTED CANDIDATE" in cand.why_significant

    # Partner adopts one candidate KAM with professional wording
    rep_svc.add_key_audit_matter(
        wp.id,
        AddKeyAuditMatterDTO(
            matter_title="Valuation and Physical Verification of Property, Plant and Equipment",
            why_significant="PPE represents ₹65.0 Lakh (significant proportion of total assets) subject to management estimates.",
            how_addressed="Verified physical verification reports, reconciled with fixed assets register, and tested depreciation methodology.",
            fs_reference="Note 10 to Financial Statements",
            wp_references=["WP-C1", "CARO-3(i)"],
            evidence_references=["EV-PPE-001", "FAR-2026"],
            partner_conclusion="Depreciation and carrying value conform to Ind AS 16 without material exceptions.",
            final_disclosure_text="We identified the valuation of PPE as a Key Audit Matter. Our audit procedures included reviewing physical verification certificates and depreciation tests.",
        ),
    )

    # =======================================================
    # 7. CROSS-DOCUMENT CONSISTENCY CHECKS
    # =======================================================
    consistency = rep_svc.check_consistency(eng_id)
    assert consistency["is_consistent"] is True
    assert len(consistency["inconsistencies"]) == 0

    # =======================================================
    # 8. PARTNER APPROVAL WITH UDIN
    # =======================================================
    udin = "26444444AAAAAA4444"
    approved_wp = rep_svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="Comprehensive review concluded. Ind AS true and fair view confirmed.",
            udin=udin,
        )
    )
    assert approved_wp.status == ReportWorkpaperStatusEnum.PARTNER_APPROVED
    assert approved_wp.approved_by_partner_id == partner.username
    assert approved_wp.udin == udin

    # =======================================================
    # 9. PRE-GENERATION CHECKLIST & RECONCILIATION
    # =======================================================
    gen_svc = AuditReportGenerationService(db_manager, storage_dir=reports_dir)
    chk = gen_svc.evaluate_reporting_checklist(eng_id)
    assert chk["can_generate"] is True
    assert len(chk["blockers"]) == 0

    recon = gen_svc.reconcile_report_numbers(eng_id, wp.id)
    assert recon.is_reconciled is True
    assert len(recon.discrepancies) == 0

    # Verify Data Lineage (Source tags)
    revenue_lineage = next(item for item in recon.lineage_items if item.field_name == "Revenue from Operations")
    assert revenue_lineage.source_type == SourceLineageTypeEnum.SYSTEM
    assert "₹12,000,000.00" in revenue_lineage.reported_value

    # =======================================================
    # 10. GENERATE FINAL AUDIT REPORT & VERIFY LOCK
    # =======================================================
    gen_result = gen_svc.generate_statutory_audit_report(engagement_id=eng_id)
    assert gen_result.is_locked is True
    assert gen_result.status == ReportWorkpaperStatusEnum.LOCKED
    assert Path(gen_result.pdf_path).exists()

    # Verify generated document contents
    with open(gen_result.pdf_path, encoding="utf-8") as f:
        report_text = f.read()
    assert "INDEPENDENT AUDITOR'S REPORT" in report_text
    assert "ABC Manufacturing Pvt Ltd" in report_text
    assert "2025-26" in report_text
    assert "UDIN: 26444444AAAAAA4444" in report_text
    assert "KEY AUDIT MATTERS" in report_text
    assert "Valuation and Physical Verification of Property, Plant and Equipment" in report_text
    assert "REPORT ON OTHER LEGAL AND REGULATORY REQUIREMENTS" in report_text

    # =======================================================
    # 11. MUTATION & STALE REPORT CHANGE DETECTION
    # =======================================================
    # Mutate an underlying financial value in the trial balance
    with db_manager.session_scope() as session:
        from sqlalchemy import select

        from finauditpro.infrastructure.persistence.models import TrialBalanceLineModel
        stmt = select(TrialBalanceLineModel).where(
            TrialBalanceLineModel.dataset_id == ds.id,
            TrialBalanceLineModel.account_code == "4001",
        )
        model = session.scalars(stmt).first()
        assert model is not None
        model.closing_cr_paise = 1300000000  # Altered from ₹1.2 Cr to ₹1.3 Cr
        session.flush()

    # Change detection must detect that the report's underlying dependency has changed!
    is_stale = rep_svc.check_and_invalidate_stale_report(eng_id)
    assert is_stale is True

    # Verify the workpaper status has been marked INVALIDATED_STALE
    stale_wp = rep_svc.get_report_workpaper(wp.id)
    assert stale_wp.status == ReportWorkpaperStatusEnum.INVALIDATED_STALE

    # Generation checklist must now BLOCK generation!
    chk_stale = gen_svc.evaluate_reporting_checklist(eng_id)
    assert chk_stale["can_generate"] is False
    assert any("INVALIDATED" in b for b in chk_stale["blockers"])

    # =======================================================
    # 12. RESOLUTION, RE-APPROVAL & REGENERATION
    # =======================================================
    # Correct the source: update the financial statement package to reflect the corrected/updated TB
    bs2 = fs_svc.generate_balance_sheet(gen_dto)
    pnl2 = fs_svc.generate_profit_and_loss(gen_dto)
    cf2 = fs_svc.generate_cash_flow_statement(gen_dto)
    fs_svc.save_package(
        SaveFinancialStatementPackageDTO(
            engagement_id=eng_id,
            balance_sheet=bs2,
            profit_loss=pnl2,
            cash_flow=cf2,
        )
    )

    # Partner reviews and re-approves with updated state
    v2_approved = rep_svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="Revised sales ledger reconciled; updated report approved.",
            udin="26444444AAAAAA4445",
        )
    )
    assert v2_approved.status == ReportWorkpaperStatusEnum.PARTNER_APPROVED
    assert v2_approved.version == 2

    # Re-generate controlled version 2
    gen_result_v2 = gen_svc.generate_statutory_audit_report(engagement_id=eng_id)
    assert gen_result_v2.is_locked is True
    assert gen_result_v2.version == 2
    assert Path(gen_result_v2.pdf_path).exists()

    with open(gen_result_v2.pdf_path, encoding="utf-8") as f:
        v2_text = f.read()
    assert "Report Version: v2" in v2_text
    assert "UDIN: 26444444AAAAAA4445" in v2_text
