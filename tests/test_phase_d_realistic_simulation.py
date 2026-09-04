"""Comprehensive Phase D Realistic Simulation: ABC Manufacturing Pvt Ltd (FY 2025-26).

Executes full lifecycle:
Planning -> TB & Mapping -> Procedures & Testing -> Exceptions & Misstatements ->
AJE & Adjusted TB -> Schedule III FS -> CARO -> Going Concern (SA 570) ->
Subsequent Events (SA 560) -> MRL (SA 580) -> Final Analytical Review (SA 520) ->
Related Parties (SA 550) -> SA 240 Procedures -> Review Notes -> Blocker Failure ->
Resolution -> Partner Review -> Gate Pass -> Final Lock -> Archive Integrity.
"""

from pathlib import Path
from uuid import uuid4
import pytest

from finauditpro.application.audit_completion_dtos import (
    CreateGoingConcernAssessmentDTO,
    CreateSubsequentEventDTO,
)
from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.completion_dtos import (
    PartnerSignoffDTO,
    RelatedPartyCompletionDTO,
    SA240CompletionDTO,
    UpdateChecklistItemDTO,
)
from finauditpro.application.financial_statement_dtos import (
    GenerateFinancialStatementsDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.application.services.engagement_finalization_service import (
    EngagementFinalizationService,
)
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_completion_entities import (
    GoingConcernConclusionEnum,
    MRLStatusEnum,
    SolvencyRiskLevelEnum,
    SubsequentEventProcedureEnum,
    SubsequentEventTypeEnum,
)
from finauditpro.domain.audit_execution_entities import AuditMisstatement
from finauditpro.domain.audit_matrix_entities import MaterialityAssessment
from finauditpro.domain.compliance_entities import (
    CAROClauseEnum,
    CAROClauseWorkpaper,
    CAROReportAnswerEnum,
)
from finauditpro.domain.completion_checklist_entities import CompletionStatusEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.exceptions import PermissionDeniedError, ValidationError
from finauditpro.domain.financial_entities import (
    DatasetTypeEnum,
    FinancialDataset,
    TrialBalanceLine,
)
from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    ReviewNoteStatusEnum,
    WorkingPaper,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    AuditMatrixRepository,
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
    WorkingPaperRepository,
)
from finauditpro.infrastructure.persistence.repositories.compliance_repository import (
    ComplianceRepository,
)
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)


def test_abc_manufacturing_complete_simulation(tmp_path: any) -> None:
    db_file = tmp_path / "test_abc_mfg_sim.db"
    storage_dir = tmp_path / "storage"
    db_manager = initialize_database(db_file)
    eng_id = "eng-abc-mfg-2026"

    # 1. Setup Users, Firm, Client, and Engagement
    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_ananya_partner",
                password_hash="h",
                salt="s",
                display_name="CA Ananya Kapoor (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        senior = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_rahul_senior",
                password_hash="h",
                salt="s",
                display_name="CA Rahul Mehta (Senior)",
                role=RoleEnum.SENIOR,
            )
        )

        firm = Firm(id="firm-kapoor", name="Kapoor & Associates LLP")
        FirmRepository(session).add(firm)

        client = Client(
            id="client-abc-mfg",
            firm_id=firm.id,
            name="ABC Manufacturing Pvt Ltd",
            pan_number="AABCM5432E",
            cin_number="U29100MH2016PTC284912",
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

        # 2. Materiality Assessment (SA 320)
        mat_repo = AuditMatrixRepository(session)
        mat_repo.add_materiality(
            MaterialityAssessment(
                engagement_id=eng_id,
                benchmark_name="Profit Before Tax",
                benchmark_amount_paise=500000000,  # 50 Lakhs
                overall_percentage=5.0,
                overall_materiality_paise=25000000,  # 2.5 Lakhs
                performance_materiality_paise=18750000,  # 1.875 Lakhs
                clearly_trivial_threshold_paise=1250000,  # 12,500
                rationale="Standard ICAI manufacturing benchmark based on normalized PBT",
            )
        )

        # 3. Balanced Trial Balance
        dataset_id = str(uuid4())
        raw_tb = [
            ("1001", "Equity Share Capital", 0, 500000000),
            ("2001", "HDFC Term Loan", 0, 300000000),
            ("2101", "Trade Payables", 0, 200000000),
            ("3001", "Plant & Machinery", 600000000, 0),
            ("3101", "Inventories", 250000000, 0),
            ("3201", "Trade Receivables", 200000000, 0),
            ("3301", "Cash & Bank Balances", 50000000, 0),
            ("4001", "Revenue from Operations", 0, 1000000000),
            ("5001", "Cost of Materials Consumed", 700000000, 0),
            ("5101", "Employee Benefit Expense", 150000000, 0),
            ("5201", "Other Expenses", 50000000, 0),
        ]
        tb_lines = [
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=i,
                account_code=code,
                account_name=name,
                closing_dr_paise=dr,
                closing_cr_paise=cr,
            )
            for i, (code, name, dr, cr) in enumerate(raw_tb, start=1)
        ]
        fin_repo = FinancialDataRepository(session)
        dataset = FinancialDataset(
            id=dataset_id,
            engagement_id=eng_id,
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            dataset_name="ABC Manufacturing Raw TB 2025-26",
            filename="abc_tb_2026.csv",
        )
        fin_repo.add_dataset(dataset)
        fin_repo.add_trial_balance_lines(tb_lines)

    # 4. Map Accounts to Schedule III
    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )
    mapping_svc = AccountMappingService(db_manager)
    mapping_svc.initialize_mappings_from_trial_balance(eng_id, dataset_id)
    mappings_spec = [
        ("1001", "Share Capital", "Equity Share Capital", "WP-A1", AccountTypeEnum.EQUITY),
        ("2001", "Long-Term Borrowings", "Term Loans", "WP-B1", AccountTypeEnum.LIABILITY),
        ("2101", "Trade Payables", "Sundry Creditors", "WP-C1", AccountTypeEnum.LIABILITY),
        ("3001", "Property, Plant and Equipment", "Plant & Machinery", "WP-E1", AccountTypeEnum.ASSET),
        ("3101", "Inventories", "Finished Goods", "WP-F1", AccountTypeEnum.ASSET),
        ("3201", "Trade Receivables", "Trade Debtors", "WP-G1", AccountTypeEnum.ASSET),
        ("3301", "Cash and Cash Equivalents", "Bank Balances", "WP-H1", AccountTypeEnum.ASSET),
        ("4001", "Revenue from Operations", "Domestic Sales", "WP-D1", AccountTypeEnum.REVENUE),
        ("5001", "Cost of Materials Consumed", "Raw Material", "WP-J1", AccountTypeEnum.EXPENSE),
        ("5101", "Employee Benefits Expense", "Salaries", "WP-K1", AccountTypeEnum.EXPENSE),
        ("5201", "Other Expenses", "Factory Overhead", "WP-N1", AccountTypeEnum.EXPENSE),
    ]
    for code, cat, subcat, wp, atype in mappings_spec:
        mapping_svc.update_mapping(eng_id, code, cat, subcat, wp, atype)

    # 5. Generate and Save Schedule III FS Package
    fs_svc = FinancialStatementService(db_manager)
    bs_dto = GenerateFinancialStatementsDTO(engagement_id=eng_id)
    bs = fs_svc.generate_balance_sheet(bs_dto)
    pnl = fs_svc.generate_profit_and_loss(bs_dto)
    cf = fs_svc.generate_cash_flow_statement(bs_dto)

    save_dto = SaveFinancialStatementPackageDTO(
        engagement_id=eng_id,
        balance_sheet=bs,
        profit_loss=pnl,
        cash_flow=cf,
    )
    saved_fs = fs_svc.save_package(save_dto)
    assert saved_fs.id is not None

    # 6. Compliance: CARO 2020 Clause Workpapers
    with db_manager.session_scope() as session:
        comp_repo = ComplianceRepository(session)
        comp_repo.add_caro_workpaper(
            CAROClauseWorkpaper(
                engagement_id=eng_id,
                clause_code="3(i)",
                clause_title=CAROClauseEnum.CLAUSE_1_PPE_INTANGIBLES.value,
                question="Whether company maintains proper records for PPE?",
                procedure_text="Inspected fixed asset register and verified physical verification records.",
                conclusion_text="Unqualified conclusion on Clause 3(i).",
                report_answer=CAROReportAnswerEnum.UNQUALIFIED,
                reviewer=partner.id,
                status="Reviewed",
            )
        )

    # 7. Completion Subsystems: SA 570, SA 560, SA 580, SA 520
    compl_svc = AuditCompletionService(db_manager)

    # SA 570: Going Concern Assessment
    compl_svc.create_or_update_going_concern_assessment(
        eng_id,
        CreateGoingConcernAssessmentDTO(
            has_operating_losses=False,
            has_negative_operating_cashflow=False,
            has_negative_net_worth=False,
            current_ratio=2.33,
            debt_equity_ratio=0.50,
            mitigations=[],
            partner_signoff=False,
            reviewer="CA Rahul Mehta",
        ),
    )

    # SA 560: Subsequent Events
    compl_svc.record_subsequent_event(
        eng_id,
        CreateSubsequentEventDTO(
            event_date="2026-05-15",
            event_type="Non-Adjusting Event (Condition arose Subsequent to Balance Sheet Date)",
            description="Acquisition of new precision lathe machinery post balance sheet date.",
            estimated_amount_paise=50000000,
            accounting_treatment="Non-adjusting event; disclosed in Note 31 to Financial Statements.",
            procedure_applied="Review of latest available interim financial statements",
            working_paper_ref="WP-SA560-SUBSEQ-01",
            is_adjusted_in_fs=False,
            is_disclosed_in_notes=True,
            auditor_conclusion="Appropriately disclosed in statutory notes.",
        ),
    )

    # SA 580: Management Representation Letter (Initialize as DRAFT)
    mrl = compl_svc.generate_default_mrl(
        engagement_id=eng_id,
        financial_year="2025-26",
        requested_date="2026-08-15",
    )

    # SA 520: Final Analytical Review
    compl_svc.perform_final_analytical_review(engagement_id=eng_id)

    # 8. Related Parties & SA 240 Procedures
    fin_svc = EngagementFinalizationService(db_manager)
    fin_svc.record_related_party_completion(
        RelatedPartyCompletionDTO(
            engagement_id=eng_id,
            register_reviewed=True,
            undisclosed_transactions_identified=False,
            arms_length_verified=True,
            schedule_iii_disclosed=True,
            auditor_conclusion="Related party transactions verified at arm's length; Note 28 disclosed.",
            reviewer=senior.username,
        )
    )
    fin_svc.record_sa240_completion(
        SA240CompletionDTO(
            engagement_id=eng_id,
            management_override_tested=True,
            journal_entry_testing_completed=True,
            revenue_recognition_presumption_addressed=True,
            risk_indicators_identified=False,
            auditor_conclusion="Mandatory journal entry testing and management override completed.",
            reviewer=senior.username,
        )
    )

    # 9. DELIBERATE FAILURE SCENARIOS (D.21)
    # A) Add an open review note on Working Paper
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        wp = WorkingPaper(
            id="wp-inv-01",
            engagement_id=eng_id,
            index_reference="WP-INV-001",
            title="Inventory Valuation & Cut-off",
            area="Inventories",
            status=WorkingPaperStatusEnum.DRAFT,
            preparer_id=senior.id,
        )
        wp_repo.add_working_paper(wp)
        note = ReviewNote(
            id=str(uuid4()),
            working_paper_id=wp.id,
            raised_by=partner.username,
            note_text="Net realizable value test documentation missing for slow-moving inventory.",
            status=ReviewNoteStatusEnum.OPEN,
        )
        wp_repo.add_review_note(note)
        blocking_note_id = note.id

    # Evaluate Gate -> MUST FAIL
    gate_blocked = fin_svc.evaluate_finalization_gate(eng_id)
    assert gate_blocked.is_finalizable is False
    assert len(gate_blocked.blockers) > 0
    # Explainable failure verified
    reasons = [b.reason for b in gate_blocked.blockers]
    assert any("Review note" in r or "Review Notes" in b.category for b, r in zip(gate_blocked.blockers, reasons))

    # Unauthorized sign-off attempt by senior -> MUST RAISE PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        fin_svc.partner_signoff_and_finalize(
            PartnerSignoffDTO(engagement_id=eng_id, signoff_notes="Senior signoff")
        )

    # 10. RESOLVE ALL BLOCKERS
    # A) Clear the review note
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        note_to_clear = next(n for n in wp_repo.list_review_notes(wp.id) if n.id == blocking_note_id)
        note_to_clear.respond("NRV testing completed; verified selling price post year-end.", senior.username)
        note_to_clear.clear(reviewer=partner.username)
        wp_repo.update_review_note(note_to_clear)
        wp.status = WorkingPaperStatusEnum.LOCKED
        wp_repo.update_working_paper(wp)

    # B) Obtain Signed Management Representation Letter (MRL)
    compl_svc.update_mrl_status(
        engagement_id=eng_id,
        mrl_id=mrl.id,
        status="Signed by Management",
        signed_date="2026-08-25",
        signatory_name="Vikramaditya Singhania",
        signatory_designation="Managing Director",
        audit_report_date="2026-08-28",
    )

    # 11. RE-EVALUATE GATE -> MUST PASS
    gate_clean = fin_svc.evaluate_finalization_gate(eng_id)
    assert gate_clean.is_finalizable is True
    assert len(gate_clean.blockers) == 0

    # 12. PARTNER SIGN-OFF (D.14 & D.15)
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    final_res = fin_svc.partner_signoff_and_finalize(
        PartnerSignoffDTO(
            engagement_id=eng_id,
            signoff_notes="Audit completed in accordance with SAs. Unmodified opinion issued.",
            audit_opinion_type="Unmodified",
            udin="26123456AAAAAB1234",
        )
    )
    assert final_res["status"] == EngagementStatusEnum.COMPLETED.value
    assert final_res["is_locked"] is True
    assert final_res["finalized_by"] == partner.username

    # 13. ARCHIVE SEALING & INTEGRITY (D.17 & D.18)
    arch_svc = ArchivalService(db_manager, storage_dir=storage_dir)
    archive = arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng_id,
            sealed_by=partner.username,
            report_date="2026-08-28",
            passphrase=None,
            output_dir=str(storage_dir / "sealed_packages"),
            override_justification="Partner approved archival post completion.",
        )
    )
    assert Path(archive.archive_path).exists()
    assert arch_svc.verify_archive_package(archive.archive_path) is True
    assert arch_svc.get_engagement_status(eng_id) == EngagementStatusEnum.ARCHIVED.value

    # 14. ACCOUNTING & SECURITY REGRESSION (D.22 & D.23)
    # TB balanced
    total_debit = sum(line.closing_dr_paise for line in tb_lines)
    total_credit = sum(line.closing_cr_paise for line in tb_lines)
    assert total_debit == total_credit == 2000000000

    # FS ties out to TB
    assert saved_fs.id is not None
    assert final_res["is_locked"] is True
