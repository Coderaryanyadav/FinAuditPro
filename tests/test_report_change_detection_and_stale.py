"""Integration tests for Phase E: Report Change Detection, Stale Invalidation, and Re-approval."""

from pathlib import Path
from uuid import uuid4
import pytest

from finauditpro.application.audit_report_dtos import (
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_report_generation_service import (
    AuditReportGenerationService,
)
from finauditpro.application.services.audit_report_service import AuditReportService
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
    db_file = tmp_path / "test_stale_detection.db"
    return initialize_database(db_file)


def test_report_stale_invalidation_and_reapproval(db_manager: DatabaseManager) -> None:
    eng_id = f"eng-{uuid4()}"
    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_partner_alok",
                password_hash="h",
                salt="s",
                display_name="CA Alok (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        firm = Firm(id="firm-02", name="Alok & Co")
        FirmRepository(session).add(firm)
        client = Client(id="cli-02", firm_id=firm.id, name="Zenith Logistics Ltd")
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

        # Add initial trial balance
        fin_repo = FinancialDataRepository(session)
        ds = FinancialDataset(
            id=str(uuid4()),
            engagement_id=eng_id,
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            dataset_name="TB 2025-26",
            filename="tb.csv",
        )
        fin_repo.add_dataset(ds)
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id=ds.id,
                    source_row_no=1,
                    account_code="4001",
                    account_name="Freight Revenue",
                    closing_dr_paise=0,
                    closing_cr_paise=500000000,
                ),
                TrialBalanceLine(
                    dataset_id=ds.id,
                    source_row_no=2,
                    account_code="5001",
                    account_name="Fuel Expense",
                    closing_dr_paise=500000000,
                    closing_cr_paise=0,
                ),
            ]
        )

    # 1. Partner prepares and approves report
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    svc = AuditReportService(db_manager)
    wp = svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng_id,
            reporting_framework="Companies Act 2013 / AS",
            proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
            final_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        )
    )
    approved = svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="Initial partner sign-off on unmodified report.",
        )
    )
    assert approved.status == ReportWorkpaperStatusEnum.PARTNER_APPROVED
    assert not svc.check_and_invalidate_stale_report(eng_id)

    # 2. DELIBERATE MUTATION: Modify underlying trial balance after partner approval
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_trial_balance_lines(
            [
                TrialBalanceLine(
                    dataset_id=ds.id,
                    source_row_no=3,
                    account_code="5002",
                    account_name="Late Vehicle Repair Expense",
                    closing_dr_paise=10000000,
                    closing_cr_paise=0,
                )
            ]
        )

    # 3. Change Detection -> MUST DETECT STALE & INVALIDATE
    was_invalidated = svc.check_and_invalidate_stale_report(eng_id)
    assert was_invalidated is True

    # Workpaper state check
    with db_manager.session_scope() as session:
        from finauditpro.infrastructure.persistence.repositories.audit_report_repository import (
            AuditReportRepository,
        )
        stale_wp = AuditReportRepository(session).get_report_workpaper(wp.id)
        assert stale_wp is not None
        assert stale_wp.status == ReportWorkpaperStatusEnum.INVALIDATED_STALE
        assert "modified after partner approval" in stale_wp.opinion_rationale

    # 4. Generation checklist MUST BLOCK on stale report
    gen_svc = AuditReportGenerationService(db_manager)
    checklist = gen_svc.evaluate_reporting_checklist(eng_id)
    assert checklist["can_generate"] is False
    assert any("INVALIDATED" in b for b in checklist["blockers"])

    # 5. Partner re-evaluates and re-approves with new snapshot
    wp_reapproved = svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="Re-reviewed post repair adjustment. Re-approved.",
        )
    )
    assert wp_reapproved.status == ReportWorkpaperStatusEnum.PARTNER_APPROVED
    assert not svc.check_and_invalidate_stale_report(eng_id)
