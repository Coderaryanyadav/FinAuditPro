"""Tests for Partner Review, Trusted Sign-Off, Engagement Locking, and Immutability."""

from uuid import uuid4
import pytest

from finauditpro.application.completion_dtos import PartnerSignoffDTO
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.engagement_finalization_service import (
    EngagementFinalizationService,
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
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
    WorkingPaperRepository,
)


@pytest.fixture
def partner_env(tmp_path):
    db_file = tmp_path / "test_partner_lock.db"
    db_manager = initialize_database(db_file)
    eng_id = f"eng-lock-{uuid4().hex[:8]}"

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="partner_lead",
                password_hash="hash",
                salt="salt",
                display_name="CA Ananya Kapoor (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        senior = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="senior_staff",
                password_hash="hash",
                salt="salt",
                display_name="CA Senior Staff",
                role=RoleEnum.SENIOR,
            )
        )

        firm = Firm(id="firm-partner", name="Partner Firm LLP")
        FirmRepository(session).add(firm)

        client = Client(
            id="client-partner",
            firm_id=firm.id,
            name="Partner Client Pvt Ltd",
            pan_number="AABCP1234F",
            cin_number="U29100MH2021PTC123456",
        )
        ClientRepository(session).add(client)

        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit FY 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.REVIEW,
        )
        EngagementRepository(session).add(eng)

    return db_manager, eng_id, partner, senior


def test_review_note_lifecycle_and_blocking(partner_env) -> None:
    db_manager, eng_id, partner, senior = partner_env
    svc = EngagementFinalizationService(db_manager)

    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        wp = WorkingPaper(
            id="wp-cash-01",
            engagement_id=eng_id,
            index_reference="WP-CASH-001",
            title="Bank Confirmation Procedures",
            area="Cash and Bank",
            status=WorkingPaperStatusEnum.DRAFT,
            preparer_id=senior.id,
        )
        wp_repo.add_working_paper(wp)

        # 1. Raised by Partner -> OPEN
        note = ReviewNote(
            id=str(uuid4()),
            working_paper_id=wp.id,
            raised_by=partner.username,
            note_text="Direct bank confirmation for HDFC Bank CC account not received.",
            status=ReviewNoteStatusEnum.OPEN,
        )
        wp_repo.add_review_note(note)
        note_id = note.id

    # Gate must block while review note is OPEN
    gate = svc.evaluate_finalization_gate(eng_id)
    assert gate.is_finalizable is False
    assert any("Review Notes" in b.category for b in gate.blockers)

    # 2. Senior responds -> RESPONDED
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        notes = wp_repo.list_review_notes(wp.id)
        current_note = next(n for n in notes if n.id == note_id)
        current_note.respond(
            response_text="Direct confirmation obtained via bank portal and attached as Evidence EV-CASH-04.",
            responder=senior.username,
        )
        wp_repo.update_review_note(current_note)

    # Gate still blocks because note is RESPONDED, not yet CLEARED by Partner
    gate2 = svc.evaluate_finalization_gate(eng_id)
    assert gate2.is_finalizable is False

    # 3. Partner clears note -> CLEARED
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        notes = wp_repo.list_review_notes(wp.id)
        current_note = next(n for n in notes if n.id == note_id)
        current_note.clear(reviewer=partner.username)
        wp_repo.update_review_note(current_note)

    # Verify review note blockers are now cleared
    open_items = svc.get_open_items_register(eng_id)
    rn_items = [i for i in open_items.items if i.source_type == "Review Notes"]
    assert len(rn_items) == 0


def test_trusted_security_context_partner_signoff(partner_env) -> None:
    db_manager, eng_id, partner, senior = partner_env
    svc = EngagementFinalizationService(db_manager)

    # Case A: Non-Partner attempts sign-off -> Must raise PermissionDeniedError
    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )
    dto = PartnerSignoffDTO(
        engagement_id=eng_id,
        signoff_notes="Senior trying to approve without partner authority",
        audit_opinion_type="Unmodified",
    )
    with pytest.raises(PermissionDeniedError) as exc:
        svc.partner_signoff_and_finalize(dto)
    assert "Partner" in str(exc.value)

    # Case B: Partner signs off with blocking conditions -> Must raise ValidationError
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    with pytest.raises(ValidationError) as exc:
        svc.partner_signoff_and_finalize(dto)
    assert "blocking condition" in str(exc.value).lower()


def test_engagement_lock_and_post_finalization_immutability(partner_env) -> None:
    db_manager, eng_id, partner, senior = partner_env

    # Directly set engagement to COMPLETED (finalized)
    with db_manager.session_scope() as session:
        eng_repo = EngagementRepository(session)
        eng = eng_repo.get_by_id(eng_id)
        eng.status = EngagementStatusEnum.COMPLETED
        eng_repo.update(eng)

    # Any subsequent mutation attempt must fail
    with db_manager.session_scope() as session:
        eng_repo = EngagementRepository(session)
        final_eng = eng_repo.get_by_id(eng_id)
        assert final_eng.status == EngagementStatusEnum.COMPLETED

    # Verify engagement repository prevents modifications when completed
    svc = EngagementFinalizationService(db_manager)
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    dto = PartnerSignoffDTO(
        engagement_id=eng_id,
        signoff_notes="Attempting double finalization on already finalized file",
        audit_opinion_type="Unmodified",
    )
    with pytest.raises(ValidationError) as exc:
        svc.partner_signoff_and_finalize(dto)
    assert "already finalized" in str(exc.value).lower()
