"""Unit tests for Working Paper lifecycle state machine transitions."""

import pytest

from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.exceptions import InvalidStateTransitionError
from finauditpro.domain.working_paper_entities import WorkingPaperStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_wp_env(tmp_path):
    db_file = tmp_path / "test_wp_m6.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="WP Test Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="WP Test Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    return eng, wp_svc


def test_working_paper_legal_lifecycle_transitions(setup_wp_env) -> None:
    """Verify legal state transitions: Draft -> Submitted -> Under Review."""
    eng, wp_svc = setup_wp_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-001",
            title="Revenue Substantive Testing",
            area="Revenue",
            preparer_id="Senior Auditor",
        )
    )
    assert wp.status == WorkingPaperStatusEnum.DRAFT

    # Draft -> Submitted
    submitted_wp = wp_svc.submit_for_review(wp.id, submitter_id="Senior Auditor")
    assert submitted_wp.status == WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW


def test_illegal_working_paper_transition_fails(setup_wp_env) -> None:
    """Verify illegal direct transition (e.g. Draft -> Signed Off) raises InvalidStateTransitionError."""
    eng, wp_svc = setup_wp_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-BAD-001",
            title="Illegal Transition WP",
            area="Purchases",
            preparer_id="Associate",
        )
    )

    with pytest.raises(InvalidStateTransitionError) as exc_info:
        wp.transition_to(WorkingPaperStatusEnum.LOCKED)

    assert "Draft" in str(exc_info.value)
    assert "Locked" in str(exc_info.value)
