"""Unit tests for Partner RBAC-gated engagement reopen workflow and prior archive preservation."""

import pytest

from finauditpro.application.archival_dtos import FreezeAndSealDTO, ReopenEngagementDTO
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
from finauditpro.domain.entities import EngagementStatusEnum, RoleEnum
from finauditpro.domain.exceptions import PermissionDeniedError
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import (
    ArchivalRepository,
    EngagementRepository,
)


@pytest.fixture
def setup_reopen_env(tmp_path):
    db_file = tmp_path / "test_reopen_m9.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Reopen Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Reopen Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(tmp_path / "storage"))

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-RE-01",
            title="Reopen WP",
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
            title="Reopen Report",
            generated_by="Auditor",
        )
    )
    report_svc.approve_report(
        ApproveReportDTO(report_id=rep.id, approved_by="Audit Partner", approver_role="Partner")
    )

    archive = arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Audit Partner",
            report_date="2026-03-31",
            output_dir=str(tmp_path / "archives"),
        )
    )

    return eng, archive, arch_svc, db_manager


def test_reopen_fails_for_non_partner_role(setup_reopen_env) -> None:
    """Verify non-Partner roles raise PermissionDeniedError when attempting to reopen an engagement."""
    eng, archive, arch_svc, _ = setup_reopen_env

    with pytest.raises(PermissionDeniedError) as exc_info:
        arch_svc.reopen_engagement(
            ReopenEngagementDTO(
                engagement_id=eng.id,
                reopened_by="Senior Auditor",
                user_role=RoleEnum.SENIOR,
                reason="Need to add extra note",
            )
        )
    assert "Only Audit Partners" in str(exc_info.value)


def test_reopen_success_preserves_prior_archive(setup_reopen_env) -> None:
    """Verify Partner reopen updates status to Reopened, records reason, and preserves prior archive."""
    eng, archive, arch_svc, db_manager = setup_reopen_env

    arch_svc.reopen_engagement(
        ReopenEngagementDTO(
            engagement_id=eng.id,
            reopened_by="Managing Partner",
            user_role="Partner",
            reason="Subsequent discovery of material post-balance sheet event requiring disclosure.",
        )
    )

    with db_manager.session_scope() as session:
        eng_repo = EngagementRepository(session)
        fetched_eng = eng_repo.get_by_id(eng.id)
        assert fetched_eng.status == EngagementStatusEnum.REOPENED

        arch_repo = ArchivalRepository(session)
        records = arch_repo.list_reopen_records(eng.id)
        assert len(records) == 1
        assert records[0].prior_archive_id == archive.id
        assert "Subsequent discovery" in records[0].reason
