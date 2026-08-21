"""Unit tests for multi-year audit roll-forward lifecycle, draft creation, and archive immutability."""

import pytest

from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.report_dtos import ApproveReportDTO, GenerateReportDTO
from finauditpro.application.roll_forward_dtos import ExecuteRollForwardDTO
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.roll_forward_service import RollForwardService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.entities import EngagementStatusEnum
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.documents.document_security import calculate_sha256
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import EngagementRepository


@pytest.fixture
def setup_rf_env(tmp_path):
    db_file = tmp_path / "test_rf_m10.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="RF Lifecycle Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="RF Lifecycle Client"))
    source_eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2024-25")
    )

    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(tmp_path / "storage"))
    rf_svc = RollForwardService(db_manager)

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=source_eng.id,
            index_reference="WP-01",
            title="Revenue Audit",
            area="Revenue",
            preparer_id="Senior Auditor",
        )
    )
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Audit Partner",
            user_role="Partner",
        )
    )

    tpls = report_svc.list_templates()
    rep = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=source_eng.id,
            template_id=tpls[0].id,
            title="FY 2024-25 Final Report",
            generated_by="Auditor",
        )
    )
    report_svc.approve_report(
        ApproveReportDTO(report_id=rep.id, approved_by="Audit Partner", approver_role="Partner")
    )

    archive = arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=source_eng.id,
            sealed_by="Audit Partner",
            report_date="2025-03-31",
            output_dir=str(tmp_path / "archives"),
        )
    )

    return source_eng, archive, rf_svc, db_manager, tmp_path


def test_roll_forward_creates_new_engagement_and_preserves_archive(setup_rf_env) -> None:
    """Verify roll-forward creates next FY engagement without altering prior sealed archive hash."""
    source_eng, archive, rf_svc, db_manager, tmp_path = setup_rf_env

    archive_hash_before = calculate_sha256(archive.archive_path)

    new_eng = rf_svc.roll_forward_engagement(
        ExecuteRollForwardDTO(
            source_engagement_id=source_eng.id,
            target_financial_year="2025-26",
            performed_by="Senior Auditor",
        )
    )

    archive_hash_after = calculate_sha256(archive.archive_path)
    assert archive_hash_before == archive_hash_after, (
        "Sealed prior archive hash mutated after roll-forward!"
    )

    assert new_eng.id != source_eng.id
    assert new_eng.financial_year == "2025-26"
    assert new_eng.client_id == source_eng.client_id
    assert new_eng.status == EngagementStatusEnum.PLANNING

    with db_manager.session_scope() as session:
        repo = EngagementRepository(session)
        fetched = repo.get_by_id(new_eng.id)
        assert fetched.prior_engagement_id == source_eng.id
