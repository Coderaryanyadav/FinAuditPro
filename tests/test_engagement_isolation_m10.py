"""Multi-tenant cross-client isolation tests for Milestone 10 roll-forward subsystem."""

import pytest
from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.report_dtos import ApproveReportDTO, GenerateReportDTO
from finauditpro.application.roll_forward_dtos import ExecuteRollForwardDTO
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import CreateEngagementDTO, EngagementService
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.roll_forward_service import RollForwardService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.exceptions import PermissionDeniedError
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import AuditMatrixRepository, RollForwardRepository


@pytest.fixture
def setup_isolation_m10_env(tmp_path):
    db_file = tmp_path / "test_isolation_m10.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Isolation M10 Firm"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta"))

    eng_a = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2024-25"))
    eng_b = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2024-25"))

    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(tmp_path / "storage"))
    rf_svc = RollForwardService(db_manager)

    # Seal eng_a
    wp_a = wp_svc.create_working_paper(CreateWorkingPaperDTO(engagement_id=eng_a.id, index_reference="WP-A", title="WP Alpha", area="Tax", preparer_id="Auditor A"))
    wp_svc.sign_off_working_paper(SignOffDTO(working_paper_id=wp_a.id, level=SignOffLevelEnum.FINAL_SIGN_OFF, user_id="Partner A", user_role="Partner"))

    tpls = report_svc.list_templates()
    rep_a = report_svc.generate_report(GenerateReportDTO(engagement_id=eng_a.id, template_id=tpls[0].id, title="Report Alpha", generated_by="Auditor A"))
    report_svc.approve_report(ApproveReportDTO(report_id=rep_a.id, approved_by="Partner A", approver_role="Partner"))

    arch_svc.freeze_and_seal_engagement(FreezeAndSealDTO(engagement_id=eng_a.id, sealed_by="Partner A", report_date="2025-03-31", output_dir=str(tmp_path / "archives")))

    return eng_a, eng_b, rf_svc, db_manager


def test_roll_forward_single_client_isolation(setup_isolation_m10_env) -> None:
    """Verify roll forward for Client Alpha creates a new engagement for Client Alpha and contains ZERO Client Beta data."""
    eng_a, eng_b, rf_svc, db_manager = setup_isolation_m10_env

    new_eng_a = rf_svc.roll_forward_engagement(
        ExecuteRollForwardDTO(
            source_engagement_id=eng_a.id,
            target_financial_year="2025-26",
            performed_by="Auditor A",
        )
    )

    assert new_eng_a.client_id == eng_a.client_id
    assert new_eng_a.client_id != eng_b.client_id

    with db_manager.session_scope() as session:
        rf_repo = RollForwardRepository(session)
        links_a = rf_repo.list_opening_balance_links(new_eng_a.id)
        links_b = rf_repo.list_opening_balance_links(eng_b.id)

        assert len(links_b) == 0
