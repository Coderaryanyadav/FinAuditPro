"""Comprehensive unit and domain tests for the Audit-Office Review Workflow, Segregation of Duties, and Role-Based Controls."""

import pytest

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    ReopenReviewNoteDTO,
    ReopenWorkingPaperDTO,
    RespondReviewNoteDTO,
    SignOffDTO,
)
from finauditpro.domain.entities import AuditEvent, RoleEnum
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    ReviewNoteStatusEnum,
    SignOffLevelEnum,
    WorkingPaper,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository


@pytest.fixture(autouse=True)
def clean_security():
    SecurityContext.clear()
    yield
    SecurityContext.clear()


@pytest.fixture
def review_env(tmp_path):
    db_file = tmp_path / "test_review_workflow.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    wp_svc = WorkingPaperService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Singhi & Co. Chartered Accountants"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Tata Consumer Products Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    from finauditpro.infrastructure.persistence.repositories.user_repository import UserRepository

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        user_repo.create_user_with_password("staff_user", "Password@123", role=RoleEnum.STAFF.value)
        user_repo.create_user_with_password("senior_user", "Password@123", role=RoleEnum.SENIOR.value)
        user_repo.create_user_with_password("manager_user", "Password@123", role=RoleEnum.MANAGER.value)
        user_repo.create_user_with_password("partner_user", "Password@123", role=RoleEnum.PARTNER.value)
        user_repo.create_user_with_password("admin_user", "Password@123", role=RoleEnum.ADMINISTRATOR.value)
        user_repo.create_user_with_password("staff_other", "Password@123", role=RoleEnum.STAFF.value)

    # Configure Engagement Roles: Staff, Senior, Manager, Partner, Admin
    wp_svc.assign_user_to_engagement(eng.id, "staff_user", RoleEnum.STAFF.value)
    wp_svc.assign_user_to_engagement(eng.id, "senior_user", RoleEnum.SENIOR.value)
    wp_svc.assign_user_to_engagement(eng.id, "manager_user", RoleEnum.MANAGER.value)
    wp_svc.assign_user_to_engagement(eng.id, "partner_user", RoleEnum.PARTNER.value)
    wp_svc.assign_user_to_engagement(eng.id, "admin_user", RoleEnum.ADMINISTRATOR.value)

    return eng, wp_svc, db_manager


def test_complete_audit_office_review_workflow(review_env) -> None:
    """Verify end-to-end workflow: PREPARER -> SUBMIT -> REVIEWER -> REVIEW NOTES -> RESPONSE -> CLEAR -> APPROVE -> PARTNER SIGN-OFF -> LOCK."""
    eng, wp_svc, db_manager = review_env

    # 1. PREPARER (Staff / Associate creates and prepares)
    SecurityContext.set_current_session(UserSession(user_id="staff_user", username="staff_user", role=RoleEnum.STAFF))
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-C-01",
            title="Trade Receivables Balance Confirmation",
            area="Receivables",
            preparer_id="staff_user",
        )
    )
    assert wp.status == WorkingPaperStatusEnum.DRAFT

    wp_prep = wp_svc.prepare_working_paper(wp.id, preparer_id="staff_user")
    assert wp_prep.status == WorkingPaperStatusEnum.PREPARED

    # 2. SUBMIT to Reviewer
    wp_sub = wp_svc.submit_for_review(wp.id, submitter_id="staff_user")
    assert wp_sub.status == WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW

    # 3. REVIEWER (Senior / Manager starts review)
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    wp_rev = wp_svc.start_review(wp.id, reviewer_id="senior_user")
    assert wp_rev.status == WorkingPaperStatusEnum.UNDER_REVIEW
    assert wp_rev.reviewer_id == "senior_user"

    # 4. REVIEW NOTES (Senior raises note on Section)
    note = wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="senior_user",
            note_text="Please verify debtor balance confirmations exceeding ₹50 Lakhs under SA 505.",
            section_id="sec-1",
        )
    )
    # Check all required review note properties
    assert note.author == "senior_user"
    assert note.comment == "Please verify debtor balance confirmations exceeding ₹50 Lakhs under SA 505."
    assert note.target == "sec-1"
    assert note.timestamp is not None
    assert note.status == ReviewNoteStatusEnum.OPEN
    assert note.response is None
    assert note.resolver is None

    # 5. RESPONSE (Preparer responds)
    SecurityContext.set_current_session(UserSession(user_id="staff_user", username="staff_user", role=RoleEnum.STAFF))
    resp_note = wp_svc.respond_review_note(
        RespondReviewNoteDTO(
            review_note_id=note.id,
            response_text="Direct confirmations obtained for 12 major debtors totaling 84% coverage.",
            responder="staff_user",
        )
    )
    assert resp_note.status == ReviewNoteStatusEnum.RESPONDED
    assert resp_note.response == "Direct confirmations obtained for 12 major debtors totaling 84% coverage."

    # 6. CLEAR (Senior clears the note)
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    cleared_note = wp_svc.clear_review_note(
        ClearReviewNoteDTO(
            review_note_id=note.id,
            reviewer="senior_user",
        )
    )
    assert cleared_note.status == ReviewNoteStatusEnum.CLEARED
    assert cleared_note.resolver == "senior_user"

    # 7. APPROVE (Senior / Manager approves working paper)
    approved_wp = wp_svc.approve_working_paper(wp.id, approver_id="senior_user")
    assert approved_wp.status == WorkingPaperStatusEnum.APPROVED

    # 8. PARTNER SIGN-OFF & LOCK (Partner executes final sign-off and seals)
    SecurityContext.set_current_session(UserSession(user_id="partner_user", username="partner_user", role=RoleEnum.PARTNER))
    signoff = wp_svc.partner_sign_off(wp.id, partner_id="partner_user", note="Audited in accordance with ICAI SA standards.")
    assert signoff.level == SignOffLevelEnum.FINAL_SIGN_OFF
    assert signoff.user_id == "partner_user"
    assert signoff.content_hash is not None

    final_wp = wp_svc.get_working_paper(wp.id)
    assert final_wp.status == WorkingPaperStatusEnum.LOCKED
    assert final_wp.is_locked
    assert final_wp.content_hash == signoff.content_hash

    # 9. Audit Events Verification
    with db_manager.session_scope() as session:
        events = AuditEventRepository(session).list_for_engagement(eng.id)
        actions = [e.action for e in events]
        assert any("Created" in a for a in actions)
        assert any("Prepared" in a for a in actions)
        assert any("Submitted" in a for a in actions)
        assert any("Review Started" in a for a in actions)
        assert any("Review Note Raised" in a for a in actions)
        assert any("Review Note Responded" in a for a in actions)
        assert any("Review Note Cleared" in a for a in actions)
        assert any("Approved" in a for a in actions)
        assert any("Signed Off" in a or "Locked" in a for a in actions)


def test_segregation_of_duties_preparer_cannot_approve_own_work(review_env) -> None:
    """Preparer cannot approve or sign-off their own working paper."""
    eng, wp_svc, db_manager = review_env

    # Senior prepares a working paper
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-02",
            title="Revenue Cut-Off",
            area="Revenue",
            preparer_id="senior_user",
        )
    )
    wp_svc.prepare_working_paper(wp.id, preparer_id="senior_user")
    wp_svc.submit_for_review(wp.id, submitter_id="senior_user")

    # Senior attempts to start review on own work -> FAILS
    with pytest.raises(ValidationError) as exc1:
        wp_svc.start_review(wp.id, reviewer_id="senior_user")
    assert "segregation of duties" in str(exc1.value).lower()

    # Manager starts review
    SecurityContext.set_current_session(UserSession(user_id="manager_user", username="manager_user", role=RoleEnum.MANAGER))
    wp_svc.start_review(wp.id, reviewer_id="manager_user")

    # Senior attempts to approve own work -> FAILS
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    with pytest.raises(ValidationError) as exc2:
        wp_svc.approve_working_paper(wp.id, approver_id="senior_user")
    assert "segregation of duties" in str(exc2.value).lower()

    # Senior attempts to sign off own work -> FAILS
    with pytest.raises(ValidationError) as exc3:
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id="senior_user",
                user_role="Senior",
            )
        )
    assert "segregation of duties" in str(exc3.value).lower()


def test_unauthorized_role_transitions(review_env) -> None:
    """Staff/Associate and Admin roles cannot perform professional approvals or partner sign-offs."""
    eng, wp_svc, db_manager = review_env

    SecurityContext.set_current_session(UserSession(user_id="staff_user", username="staff_user", role=RoleEnum.STAFF))
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-INV-01",
            title="Inventory Valuation",
            area="Inventory",
            preparer_id="staff_user",
        )
    )
    wp_svc.prepare_working_paper(wp.id, preparer_id="staff_user")
    wp_svc.submit_for_review(wp.id, submitter_id="staff_user")

    # 1. Staff cannot start review
    with pytest.raises(ValidationError) as exc_staff_rev:
        wp_svc.start_review(wp.id, reviewer_id="staff_user")
    assert "segregation of duties" in str(exc_staff_rev.value).lower() or "unauthorized" in str(exc_staff_rev.value).lower()

    # 2. Other staff member cannot start review either
    SecurityContext.set_current_session(UserSession(user_id="staff_other", username="staff_other", role=RoleEnum.STAFF))
    wp_svc.assign_user_to_engagement(eng.id, "staff_other", RoleEnum.STAFF.value)
    with pytest.raises(ValidationError) as exc_staff_other:
        wp_svc.start_review(wp.id, reviewer_id="staff_other")
    assert "unauthorized" in str(exc_staff_other.value).lower()

    # 3. Admin cannot start review or approve
    SecurityContext.set_current_session(UserSession(user_id="admin_user", username="admin_user", role=RoleEnum.ADMINISTRATOR))
    with pytest.raises(ValidationError) as exc_admin:
        wp_svc.start_review(wp.id, reviewer_id="admin_user")
    assert "unauthorized" in str(exc_admin.value).lower()

    # Manager starts review
    SecurityContext.set_current_session(UserSession(user_id="manager_user", username="manager_user", role=RoleEnum.MANAGER))
    wp_svc.start_review(wp.id, reviewer_id="manager_user")

    # 4. Manager cannot perform Final Partner Sign-off
    with pytest.raises(ValidationError) as exc_mgr_part:
        wp_svc.partner_sign_off(wp.id, partner_id="manager_user")
    assert "only partners" in str(exc_mgr_part.value).lower()

    # 5. Non-partner cannot reopen locked working paper
    wp_svc.approve_working_paper(wp.id, approver_id="manager_user")
    SecurityContext.set_current_session(UserSession(user_id="partner_user", username="partner_user", role=RoleEnum.PARTNER))
    wp_svc.partner_sign_off(wp.id, partner_id="partner_user")

    SecurityContext.set_current_session(UserSession(user_id="manager_user", username="manager_user", role=RoleEnum.MANAGER))
    with pytest.raises(ValidationError) as exc_reopen:
        wp_svc.reopen_working_paper(
            ReopenWorkingPaperDTO(
                working_paper_id=wp.id,
                reopened_by="manager_user",
                reason="Manager attempt",
            )
        )
    assert "only partners" in str(exc_reopen.value).lower()


def test_review_note_lifecycle_open_responded_cleared_reopened(review_env) -> None:
    """Review note transitions: OPEN -> RESPONDED -> CLEARED -> REOPENED -> RESPONDED -> CLEARED."""
    eng, wp_svc, db_manager = review_env

    SecurityContext.set_current_session(UserSession(user_id="staff_user", username="staff_user", role=RoleEnum.STAFF))
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-EXP-01",
            title="Operating Expenses Vouching",
            area="Expenses",
            preparer_id="staff_user",
        )
    )
    wp_svc.prepare_working_paper(wp.id, preparer_id="staff_user")
    wp_svc.submit_for_review(wp.id, submitter_id="staff_user")

    # Senior raises note (OPEN)
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    note = wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="senior_user",
            note_text="Missing approval signatures on travel expense vouchers > ₹1,00,000.",
        )
    )
    assert note.status == ReviewNoteStatusEnum.OPEN

    # Staff responds (RESPONDED)
    SecurityContext.set_current_session(UserSession(user_id="staff_user", username="staff_user", role=RoleEnum.STAFF))
    note_resp = wp_svc.respond_review_note(
        RespondReviewNoteDTO(
            review_note_id=note.id,
            response_text="Director approvals attached as Exhibit EXP-99.",
            responder="staff_user",
        )
    )
    assert note_resp.status == ReviewNoteStatusEnum.RESPONDED

    # Senior clears (CLEARED)
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    note_clr = wp_svc.clear_review_note(
        ClearReviewNoteDTO(
            review_note_id=note.id,
            reviewer="senior_user",
        )
    )
    assert note_clr.status == ReviewNoteStatusEnum.CLEARED

    # Senior reopens (REOPENED)
    note_reopened = wp_svc.reopen_review_note(
        ReopenReviewNoteDTO(
            review_note_id=note.id,
            reviewer="senior_user",
            reason="Exhibit EXP-99 is missing director signature for Voucher #8412.",
        )
    )
    assert note_reopened.status == ReviewNoteStatusEnum.REOPENED
    assert "[Reopened by senior_user" in note_reopened.note_text

    # Approval is now blocked because 1 reopened note exists
    with pytest.raises(ValidationError):
        wp_svc.approve_working_paper(wp.id, approver_id="senior_user")

    # Staff responds again (RESPONDED)
    SecurityContext.set_current_session(UserSession(user_id="staff_user", username="staff_user", role=RoleEnum.STAFF))
    note_resp2 = wp_svc.respond_review_note(
        RespondReviewNoteDTO(
            review_note_id=note.id,
            response_text="Uploaded signed addendum for Voucher #8412.",
            responder="staff_user",
        )
    )
    assert note_resp2.status == ReviewNoteStatusEnum.RESPONDED

    # Senior clears again (CLEARED)
    SecurityContext.set_current_session(UserSession(user_id="senior_user", username="senior_user", role=RoleEnum.SENIOR))
    note_clr2 = wp_svc.clear_review_note(
        ClearReviewNoteDTO(
            review_note_id=note.id,
            reviewer="senior_user",
        )
    )
    assert note_clr2.status == ReviewNoteStatusEnum.CLEARED

    # Approval now succeeds
    approved = wp_svc.approve_working_paper(wp.id, approver_id="senior_user")
    assert approved.status == WorkingPaperStatusEnum.APPROVED
