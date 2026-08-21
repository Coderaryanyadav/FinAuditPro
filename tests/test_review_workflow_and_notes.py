"""Unit tests for review note threading, open-notes blocking sign-off control, and segregation of duties."""

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
    RespondReviewNoteDTO,
    SignOffDTO,
)
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_review_env(tmp_path):
    db_file = tmp_path / "test_review_m6.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Review Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Review Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    return eng, wp_svc


def test_open_review_notes_block_signoff_control(setup_review_env) -> None:
    """Verify Hard Control 1: Open review notes strictly block sign-off."""
    eng, wp_svc = setup_review_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-CASH-001",
            title="Cash & Bank Testing",
            area="Cash",
            preparer_id="Preparer User",
        )
    )

    # Raise review note
    note = wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="Manager Reviewer",
            note_text="Reconcile bank balance against statement page 4.",
        )
    )

    # Attempt sign-off while note is open -> MUST FAIL
    with pytest.raises(ValidationError) as exc_info:
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="Audit Partner",
                user_role="Partner",
            )
        )
    assert "Cannot sign off Working Paper" in str(exc_info.value)

    # Respond & Clear note
    wp_svc.respond_review_note(
        RespondReviewNoteDTO(
            review_note_id=note.id,
            response_text="Attached bank reconciliation statement.",
            responder="Preparer User",
        )
    )
    wp_svc.clear_review_note(
        ClearReviewNoteDTO(
            review_note_id=note.id,
            reviewer="Manager Reviewer",
        )
    )

    # Sign-off after notes cleared -> MUST SUCCEED
    signoff = wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Audit Partner",
            user_role="Partner",
        )
    )
    assert signoff.id is not None


def test_segregation_of_duties_enforcement(setup_review_env) -> None:
    """Verify Hard Control 2: Preparer cannot perform final sign-off on their own working paper."""
    eng, wp_svc = setup_review_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-SOD-001",
            title="Segregation of Duties WP",
            area="Tax",
            preparer_id="Same User",
        )
    )

    # Preparer attempts final sign-off -> MUST FAIL
    with pytest.raises(ValidationError) as exc_info:
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="Same User",
                user_role="Partner",
            )
        )
    assert "Segregation of Duties Violation" in str(exc_info.value)
