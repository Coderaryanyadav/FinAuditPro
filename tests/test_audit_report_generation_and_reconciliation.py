"""Integration tests for Phase E: Report Checklist Gates, Lineage Reconciliation, and Document Generation."""

from pathlib import Path
from uuid import uuid4

import pytest

from finauditpro.application.audit_completion_dtos import CreateGoingConcernAssessmentDTO
from finauditpro.application.audit_report_dtos import (
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
)
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
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    ReportWorkpaperStatusEnum,
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


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "test_generation_reconciliation.db"
    return initialize_database(db_file)


def test_reporting_gates_lineage_and_generation(db_manager: DatabaseManager, tmp_path: Path) -> None:
    eng_id = f"eng-{uuid4()}"
    storage_dir = tmp_path / "reports_out"

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_partner_sumit",
                password_hash="h",
                salt="s",
                display_name="CA Sumit (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        firm = Firm(id="firm-03", name="Sumit & Associates")
        FirmRepository(session).add(firm)
        client = Client(id="cli-03", firm_id=firm.id, name="Apex Dynamics Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

        # Balanced Trial Balance
        fin_repo = FinancialDataRepository(session)
        ds = FinancialDataset(
            id=str(uuid4()),
            engagement_id=eng_id,
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            dataset_name="Apex TB",
            filename="apex_tb.csv",
        )
        fin_repo.add_dataset(ds)
        tb_lines = [
            ("1001", "Equity Capital", 0, 500000000),
            ("2001", "Bank Loan", 0, 200000000),
            ("3001", "Plant Machinery", 400000000, 0),
            ("3301", "Bank Balance", 300000000, 0),
            ("4001", "Revenue", 0, 800000000),
            ("5001", "Raw Materials", 800000000, 0),
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

    # 1. Map Accounts & Generate FS Package
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    map_svc = AccountMappingService(db_manager)
    map_svc.initialize_mappings_from_trial_balance(eng_id, ds.id)
    map_svc.update_mapping(eng_id, "1001", "Share Capital", "Equity", "WP-A", AccountTypeEnum.EQUITY)
    map_svc.update_mapping(eng_id, "2001", "Long-Term Borrowings", "Loans", "WP-B", AccountTypeEnum.LIABILITY)
    map_svc.update_mapping(eng_id, "3001", "Property, Plant and Equipment", "Machinery", "WP-C", AccountTypeEnum.ASSET)
    map_svc.update_mapping(eng_id, "3301", "Cash and Cash Equivalents", "Bank", "WP-D", AccountTypeEnum.ASSET)
    map_svc.update_mapping(eng_id, "4001", "Revenue from Operations", "Sales", "WP-E", AccountTypeEnum.REVENUE)
    map_svc.update_mapping(eng_id, "5001", "Cost of Materials Consumed", "Materials", "WP-F", AccountTypeEnum.EXPENSE)

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

    # 2. Check Reporting Checklist BEFORE completion items -> MUST FAIL
    gen_svc = AuditReportGenerationService(db_manager, storage_dir=storage_dir)
    chk_initial = gen_svc.evaluate_reporting_checklist(eng_id)
    assert chk_initial["can_generate"] is False
    assert any("Going Concern" in b for b in chk_initial["blockers"])
    assert any("Management Representation" in b for b in chk_initial["blockers"])
    assert any("workpaper has not been prepared" in b for b in chk_initial["blockers"])

    # 3. Complete Going Concern & MRL
    compl_svc = AuditCompletionService(db_manager)
    compl_svc.create_or_update_going_concern_assessment(
        eng_id,
        CreateGoingConcernAssessmentDTO(
            has_operating_losses=False,
            has_negative_operating_cashflow=False,
            has_negative_net_worth=False,
            current_ratio=2.5,
            debt_equity_ratio=0.4,
            mitigations=[],
            partner_signoff=True,
            reviewer="CA Sumit",
        ),
    )
    mrl = compl_svc.generate_default_mrl(eng_id, "2025-26", "2026-08-15")
    compl_svc.update_mrl_status(
        engagement_id=eng_id,
        mrl_id=mrl.id,
        status="Signed Representation Letter Obtained",
        signed_date="2026-08-25",
        signatory_name="Rahul Gupta",
        signatory_designation="Director",
        audit_report_date="2026-08-28",
    )

    # 4. Prepare and Approve Audit Report Workpaper
    rep_svc = AuditReportService(db_manager)
    wp = rep_svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng_id,
            reporting_framework="Companies Act 2013 / Ind AS",
            proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
            final_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        )
    )
    rep_svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="All documentation verified; unqualified report approved.",
            udin="26555555AAAAAB5555",
        )
    )

    # 5. Check Reporting Checklist -> MUST PASS
    chk_passed = gen_svc.evaluate_reporting_checklist(eng_id)
    assert chk_passed["can_generate"] is True
    assert len(chk_passed["blockers"]) == 0

    # 6. Reconcile Report Numbers and Lineage
    recon = gen_svc.reconcile_report_numbers(eng_id, wp.id)
    assert recon.is_reconciled is True
    assert recon.reconciled_items_count == 6
    assert recon.unreconciled_items_count == 0
    lineage_fields = [item.field_name for item in recon.lineage_items]
    assert "Revenue from Operations" in lineage_fields
    assert "Total Assets" in lineage_fields
    assert "Cash & Bank Balances" in lineage_fields

    # 7. Generate Statutory Audit Report Document
    gen_result = gen_svc.generate_statutory_audit_report(eng_id)
    assert gen_result.is_locked is True
    assert gen_result.status == ReportWorkpaperStatusEnum.LOCKED
    assert Path(gen_result.pdf_path).exists()
    assert len(gen_result.content_hash) == 64
