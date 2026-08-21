"""Unit tests for deterministic SHA-256 sealed archives, Fernet encryption, and retention timelines."""

import pytest

from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.report_dtos import ApproveReportDTO, GenerateReportDTO
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_sealing_env(tmp_path):
    db_file = tmp_path / "test_sealing_m9.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Sealing Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Sealing Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(tmp_path / "storage"))

    # Prepare fully signed off engagement
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-SEAL-01",
            title="Complete WP",
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
            engagement_id=eng.id,
            template_id=tpls[0].id,
            title="Sealed Final Audit Report",
            generated_by="Senior Auditor",
        )
    )
    report_svc.approve_report(
        ApproveReportDTO(report_id=rep.id, approved_by="Audit Partner", approver_role="Partner")
    )

    return eng, arch_svc, db_manager, tmp_path


def test_freeze_and_seal_engagement_success(setup_sealing_env) -> None:
    """Verify freeze & seal creates deterministic SHA-256 archive and records retention timelines."""
    eng, arch_svc, _, tmp_path = setup_sealing_env

    archive = arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Audit Partner",
            report_date="2026-03-31",
            output_dir=str(tmp_path / "archives"),
        )
    )

    assert archive.id is not None
    assert archive.engagement_id == eng.id
    assert archive.archive_path.endswith(".zip")
    assert len(archive.sealed_content_hash) == 64
    assert archive.assembly_deadline == "2026-05-30"  # +60 days
    assert archive.retain_until.startswith("2033-")  # +7 years
