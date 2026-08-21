"""Unit tests for pre-archive readiness checks and override justification requirements."""

import pytest

from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
)
from finauditpro.domain.exceptions import ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_readiness_env(tmp_path):
    db_file = tmp_path / "test_readiness_m9.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Readiness Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Readiness Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(tmp_path / "storage"))

    return eng, wp_svc, arch_svc, db_manager, tmp_path


def test_readiness_check_fails_with_unsigned_working_paper(setup_readiness_env) -> None:
    """Verify readiness check flags hard failure when working papers are not signed off."""
    eng, wp_svc, arch_svc, _, _ = setup_readiness_env

    # Create unsigned working paper
    wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-01",
            title="Unsigned WP",
            area="Assets",
            preparer_id="Senior Auditor",
        )
    )

    readiness = arch_svc.run_readiness_check(eng.id)
    assert readiness.is_ready_to_seal is False
    assert readiness.has_hard_failures is True

    with pytest.raises(ValidationError) as exc_info:
        arch_svc.freeze_and_seal_engagement(
            FreezeAndSealDTO(
                engagement_id=eng.id,
                sealed_by="Partner",
                report_date="2026-03-31",
            )
        )
    assert "Hard readiness check failures exist" in str(exc_info.value)


def test_readiness_check_fails_with_open_review_note(setup_readiness_env) -> None:
    """Verify readiness check flags hard failure when open review notes exist."""
    eng, wp_svc, arch_svc, _, _ = setup_readiness_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-02",
            title="WP with Note",
            area="Liabilities",
            preparer_id="Senior Auditor",
        )
    )

    wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="Reviewer",
            note_text="Please verify opening balance.",
        )
    )

    readiness = arch_svc.run_readiness_check(eng.id)
    assert readiness.has_hard_failures is True
    assert any(
        "Open Review Notes" in item.item_name and not item.is_passed for item in readiness.items
    )
