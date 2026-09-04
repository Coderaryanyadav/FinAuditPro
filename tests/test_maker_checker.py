"""Unit and E2E tests for Phase 2 Maker-Checker review controls and versioning."""

import pytest

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
    ReopenWorkingPaperDTO,
    SignOffDTO,
)
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.working_paper_entities import (
    SignOffLevelEnum,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.working_paper_models import WorkingPaperVersionModel


@pytest.fixture
def setup_maker_checker_env(tmp_path):
    db_file = tmp_path / "test_maker_checker.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    wp_svc = WorkingPaperService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="CA Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Co"))

    # Create users in database first
    from finauditpro.infrastructure.persistence.repositories.user_repository import UserRepository

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        user_repo.create_user_with_password("usera@cafirm.com", "Password@123", role="Associate")
        user_repo.create_user_with_password("userb@cafirm.com", "Password@123", role="Senior")
        user_repo.create_user_with_password("partner@cafirm.com", "Password@123", role="Partner")

    # Engagement X (User A is Preparer, User B is Reviewer)
    eng_x = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    # Engagement Y (User A is Reviewer, User B is Preparer)
    eng_y = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2026-27")
    )

    # Setup engagement membership roles
    wp_svc.assign_user_to_engagement(eng_x.id, "usera@cafirm.com", "Associate")
    wp_svc.assign_user_to_engagement(eng_x.id, "userb@cafirm.com", "Senior")
    wp_svc.assign_user_to_engagement(eng_x.id, "partner@cafirm.com", "Partner")

    wp_svc.assign_user_to_engagement(eng_y.id, "usera@cafirm.com", "Senior")
    wp_svc.assign_user_to_engagement(eng_y.id, "userb@cafirm.com", "Associate")
    wp_svc.assign_user_to_engagement(eng_y.id, "partner@cafirm.com", "Partner")

    return eng_x, eng_y, wp_svc, db_manager


def test_engagement_level_role_resolution(setup_maker_checker_env) -> None:
    """Verify that user role resolves correctly per engagement scope."""
    eng_x, eng_y, wp_svc, db_manager = setup_maker_checker_env

    with db_manager.session_scope() as session:
        # User A is Associate in Engagement X, Senior in Y
        role_x = wp_svc._resolve_user_role(session, eng_x.id, "usera@cafirm.com")
        role_y = wp_svc._resolve_user_role(session, eng_y.id, "usera@cafirm.com")
        assert role_x == "Associate"
        assert role_y == "Senior"


def test_segregation_of_duties_prevents_self_approval(setup_maker_checker_env) -> None:
    """Verify that preparer is strictly blocked from self-review and self-approval."""
    eng_x, _, wp_svc, _ = setup_maker_checker_env

    # User B is Senior (reviewer role) but prepares this paper
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_x.id,
            index_reference="WP-A-01",
            title="Cash Reconciliation",
            area="Cash",
            preparer_id="userb@cafirm.com",
        )
    )

    wp_svc.prepare_working_paper(wp.id, "userb@cafirm.com")
    wp_svc.submit_for_review(wp.id, "userb@cafirm.com")

    # Preparer attempts to start own review -> fails
    with pytest.raises(ValidationError, match="Segregation of Duties Violation"):
        wp_svc.start_review(wp.id, "userb@cafirm.com")

    # Start review by Partner
    wp_svc.start_review(wp.id, "partner@cafirm.com")

    # Preparer attempts to sign off own paper -> fails
    with pytest.raises(ValidationError, match="Segregation of Duties Violation"):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id="userb@cafirm.com",
                user_role="Senior",
            )
        )


def test_review_note_clearance_blocking(setup_maker_checker_env) -> None:
    """Verify that final sign-off is blocked while open review points remain."""
    eng_x, _, wp_svc, _ = setup_maker_checker_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_x.id,
            index_reference="WP-B-01",
            title="Revenue Audit",
            area="Revenue",
            preparer_id="usera@cafirm.com",
        )
    )

    wp_svc.prepare_working_paper(wp.id, "usera@cafirm.com")
    wp_svc.submit_for_review(wp.id, "usera@cafirm.com")
    wp_svc.start_review(wp.id, "userb@cafirm.com")

    # Reviewer raises a review note
    note = wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="userb@cafirm.com",
            note_text="Provide supporting invoice for entry #4.",
        )
    )

    # Approve attempts must fail while note is open
    with pytest.raises(ValidationError, match="Audit Quality Violation"):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id="userb@cafirm.com",
                user_role="Senior",
            )
        )

    # Associate cannot clear note -> fails
    with pytest.raises(ValidationError, match="Cannot clear someone else's review note"):
        wp_svc.clear_review_note(
            ClearReviewNoteDTO(
                review_note_id=note.id,
                reviewer="usera@cafirm.com",
            )
        )


def test_versioning_and_historical_archive_on_return_and_reopen(setup_maker_checker_env) -> None:
    """Verify returned edits and partner reopens increment versions and archive previous states."""
    eng_x, _, wp_svc, db_manager = setup_maker_checker_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_x.id,
            index_reference="WP-C-01",
            title="Statutory Audits",
            area="Statutory Dues",
            preparer_id="usera@cafirm.com",
        )
    )

    # Transition to Under Review
    wp_svc.prepare_working_paper(wp.id, "usera@cafirm.com")
    wp_svc.submit_for_review(wp.id, "usera@cafirm.com")
    wp_svc.start_review(wp.id, "userb@cafirm.com")

    # Reviewer returns it
    wp_svc.return_working_paper(wp.id, "userb@cafirm.com")
    wp_re = wp_svc.get_working_paper(wp.id)
    assert wp_re.status == WorkingPaperStatusEnum.RETURNED

    # Preparer modifies content -> auto archives version 1, increments to version 2
    wp_svc.update_working_paper_content(
        wp_id=wp.id,
        title="Statutory Audits v2",
        area="Statutory Dues",
        conclusion="Updated statutory reconciliation.",
        sections_list=[{"title": "Scope", "content_markdown": "Test"}],
        editor_id="usera@cafirm.com",
    )

    # Assert history exists
    with db_manager.session_scope() as session:
        hist = session.query(WorkingPaperVersionModel).filter_by(working_paper_id=wp.id).all()
        assert len(hist) == 1
        assert hist[0].version == 1
        assert hist[0].title == "Statutory Audits"

    # Re-verify and sign off
    wp_svc.prepare_working_paper(wp.id, "usera@cafirm.com")
    wp_svc.submit_for_review(wp.id, "usera@cafirm.com")
    wp_svc.start_review(wp.id, "userb@cafirm.com")

    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.REVIEWED,
            user_id="userb@cafirm.com",
            user_role="Senior",
        )
    )
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="partner@cafirm.com",
            user_role="Partner",
        )
    )

    # Locked editing must fail
    with pytest.raises(ValidationError, match="Working Paper is locked"):
        wp_svc.update_working_paper_content(
            wp_id=wp.id,
            title="Statutory Audits Locked Edit",
            area="Statutory Dues",
            conclusion="Illegal edit",
            sections_list=[],
            editor_id="usera@cafirm.com",
        )

    # Reopen paper by Partner -> auto archives version 2, increments to version 3
    wp_svc.reopen_working_paper(
        ReopenWorkingPaperDTO(
            working_paper_id=wp.id,
            reopened_by="partner@cafirm.com",
            reason="Additional audit evidence.",
        )
    )

    reopened = wp_svc.get_working_paper(wp.id)
    assert reopened.version == 3
    assert reopened.is_locked is False

    with db_manager.session_scope() as session:
        hist = (
            session.query(WorkingPaperVersionModel)
            .filter_by(working_paper_id=wp.id)
            .order_by(WorkingPaperVersionModel.version)
            .all()
        )
        assert len(hist) == 2
        assert hist[0].version == 1
        assert hist[1].version == 2
        assert hist[1].title == "Statutory Audits v2"
