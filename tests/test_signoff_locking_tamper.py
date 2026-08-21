"""Unit tests for SHA-256 content hash binding, immutable locking, tamper detection, and reopening."""

import pytest

from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    CreateWorkingPaperDTO,
    ReopenWorkingPaperDTO,
    SignOffDTO,
)
from finauditpro.domain.working_paper_entities import SignOffLevelEnum, WorkingPaperStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


@pytest.fixture
def setup_tamper_env(tmp_path):
    db_file = tmp_path / "test_tamper_m6.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Tamper Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Tamper Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    return eng, wp_svc, db_manager


def test_signoff_content_hash_binding_and_tamper_detection(setup_tamper_env) -> None:
    """Verify sign-off binds to content hash and content modifications trigger loud TAMPER ALERT."""
    eng, wp_svc, db_manager = setup_tamper_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-FA-001",
            title="Fixed Assets Substantive Testing",
            area="Fixed Assets",
            preparer_id="Senior Auditor",
        )
    )

    # 1. Execute Sign-off
    signoff = wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Partner User",
            user_role="Partner",
        )
    )
    assert signoff.content_hash is not None

    # 2. Verify clean integrity check
    is_valid, msg = wp_svc.verify_integrity(wp.id)
    assert is_valid is True
    assert "Integrity Verified" in msg

    # 3. Simulate unauthorized database tampering on paper conclusion
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        wp_entity = wp_repo.get_working_paper(wp.id)
        wp_entity.conclusion = "TAMPERED CONCLUSION TEXT"
        wp_repo.update_working_paper(wp_entity)

    # 4. Verify tamper detection flags mismatch loudly
    is_valid_after, tamper_msg = wp_svc.verify_integrity(wp.id)
    assert is_valid_after is False
    assert "TAMPER ALERT" in tamper_msg


def test_reopen_locked_working_paper_preserves_version_history(setup_tamper_env) -> None:
    """Verify reopening a locked working paper increments version and audits reason."""
    eng, wp_svc, _ = setup_tamper_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REOPEN-001",
            title="Reopen Test Working Paper",
            area="Tax",
            preparer_id="Preparer A",
        )
    )

    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Partner B",
            user_role="Partner",
        )
    )

    reopened_wp = wp_svc.reopen_working_paper(
        ReopenWorkingPaperDTO(
            working_paper_id=wp.id,
            reopened_by="Quality Partner",
            reason="Additional FY26 tax assessment notice received.",
        )
    )

    assert reopened_wp.version == 2
    assert reopened_wp.is_locked is False
    assert reopened_wp.status == WorkingPaperStatusEnum.REOPENED
