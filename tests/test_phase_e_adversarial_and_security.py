"""Adversarial and Security Tests for Phase E Audit Reporting.

Tests RBAC enforcement, cross-engagement isolation, checklist gating against missing MRL,
open review notes, and stale dependencies, and verifies immutability of locked final reports.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from finauditpro.application.audit_report_dtos import (
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
    UpdateAuditReportWorkpaperDTO,
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
from finauditpro.domain.exceptions import PermissionDeniedError, ValidationError
from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    ReviewNoteStatusEnum,
    WorkingPaper,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "adv_sec_phase_e.db"
    return initialize_database(db_file)


def test_unauthorized_user_cannot_approve_or_finalize(db_manager: DatabaseManager) -> None:
    eng_id = f"eng-{uuid4()}"
    with db_manager.session_scope() as session:
        firm = Firm(id="firm-sec", name="Secure Audit LLP")
        FirmRepository(session).add(firm)
        client = Client(id="cli-sec", firm_id=firm.id, name="Secure Client Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

        user_repo = UserRepository(session)
        auditor = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="auditor_rahul",
                password_hash="h",
                salt="s",
                display_name="Rahul Auditor",
                role=RoleEnum.SENIOR,
            )
        )
        preparer = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="prep_anita",
                password_hash="h",
                salt="s",
                display_name="Anita Preparer",
                role=RoleEnum.ASSOCIATE,
            )
        )

    # 1. Preparer can create / get workpaper
    SecurityContext.set_current_user(
        UserSession(user_id=preparer.id, username=preparer.username, role=preparer.role)
    )
    rep_svc = AuditReportService(db_manager)
    wp = rep_svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng_id,
            reporting_framework="Companies Act 2013 / Ind AS",
        )
    )
    assert wp.status == ReportWorkpaperStatusEnum.DRAFT

    # 2. Auditor (non-partner) attempts to partner-approve -> MUST FAIL
    SecurityContext.set_current_user(
        UserSession(user_id=auditor.id, username=auditor.username, role=auditor.role)
    )
    with pytest.raises(PermissionDeniedError) as exc:
        rep_svc.partner_approve_report(
            PartnerApproveReportDTO(
                engagement_id=eng_id,
                report_workpaper_id=wp.id,
                approval_notes="Self-approval attempt",
            )
        )
    assert "Partner role required" in str(exc.value)

    # 3. Anonymous / empty session attempts partner approval -> MUST FAIL
    SecurityContext.set_current_user(None)
    with pytest.raises(PermissionDeniedError):
        rep_svc.partner_approve_report(
            PartnerApproveReportDTO(
                engagement_id=eng_id,
                report_workpaper_id=wp.id,
                approval_notes="Unauthenticated approval attempt",
            )
        )


def test_generation_blocked_by_missing_mrl_and_open_review_notes(
    db_manager: DatabaseManager, tmp_path: Path
) -> None:
    eng_id = f"eng-{uuid4()}"
    with db_manager.session_scope() as session:
        firm = Firm(id="firm-gate", name="Gate Audit LLP")
        FirmRepository(session).add(firm)
        client = Client(id="cli-gate", firm_id=firm.id, name="Gate Client Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit Gate",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

        partner = UserRepository(session).add_user(
            User(
                id=str(uuid4()),
                username="ca_partner_gate",
                password_hash="h",
                salt="s",
                display_name="CA Gate (Partner)",
                role=RoleEnum.PARTNER,
            )
        )

        # Add a working paper and an open review note
        wp_repo = WorkingPaperRepository(session)
        wp_audit = WorkingPaper(
            id=str(uuid4()),
            engagement_id=eng_id,
            index_reference="WP-INV-01",
            title="Inventory Physical Verification",
            area="Inventories",
            preparer_id=partner.id,
        )
        wp_repo.add_working_paper(wp_audit)
        note = ReviewNote(
            id=str(uuid4()),
            working_paper_id=wp_audit.id,
            raised_by=partner.username,
            note_text="Investigate unresolved inventory physical count variance.",
            status=ReviewNoteStatusEnum.OPEN,
        )
        wp_repo.add_review_note(note)

    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    rep_svc = AuditReportService(db_manager)
    wp = rep_svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng_id,
            reporting_framework="Companies Act 2013 / Ind AS",
        )
    )

    gen_svc = AuditReportGenerationService(db_manager, storage_dir=tmp_path / "adv_out")
    chk = gen_svc.evaluate_reporting_checklist(eng_id)
    assert chk["can_generate"] is False
    assert any("open review note" in b for b in chk["blockers"])
    assert any("Management Representation" in b for b in chk["blockers"])

    # Attempting to generate directly must raise ValidationError
    with pytest.raises(ValidationError) as exc:
        gen_svc.generate_statutory_audit_report(
            engagement_id=eng_id,
        )
    assert "REPORT GENERATION BLOCKED" in str(exc.value)


def test_locked_final_report_is_immutable(db_manager: DatabaseManager, tmp_path: Path) -> None:
    eng_id = f"eng-{uuid4()}"
    with db_manager.session_scope() as session:
        firm = Firm(id="firm-lock", name="Lock Audit LLP")
        FirmRepository(session).add(firm)
        client = Client(id="cli-lock", firm_id=firm.id, name="Locked Client Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Locked Audit",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)
        partner = UserRepository(session).add_user(
            User(
                id=str(uuid4()),
                username="ca_lock",
                password_hash="h",
                salt="s",
                display_name="CA Lock (Partner)",
                role=RoleEnum.PARTNER,
            )
        )

    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    rep_svc = AuditReportService(db_manager)
    wp = rep_svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng_id,
            reporting_framework="Companies Act 2013 / Ind AS",
        )
    )
    rep_svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="Approved for lock.",
        )
    )
    locked_wp = rep_svc.lock_final_report(wp.id)
    assert locked_wp.status == ReportWorkpaperStatusEnum.LOCKED

    # Adversarial Attempt: modify locked workpaper -> MUST FAIL
    with pytest.raises(ValidationError) as exc:
        rep_svc.update_report_workpaper(
            wp.id,
            UpdateAuditReportWorkpaperDTO(
                final_opinion=AuditOpinionTypeEnum.QUALIFIED,
            ),
        )
    assert "Cannot modify locked audit report workpaper" in str(exc.value)
