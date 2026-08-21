"""Unit tests for carried-forward audit findings provenance and M5 AI badge preservation."""

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
from finauditpro.domain.audit_matrix_entities import AuditFinding, FindingSourceEnum, FindingStatusEnum, RiskSeverityEnum
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import AuditMatrixRepository


@pytest.fixture
def setup_findings_env(tmp_path):
    db_file = tmp_path / "test_findings_m10.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Findings Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Findings Client"))
    source_eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2024-25")
    )

    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(tmp_path / "storage"))
    rf_svc = RollForwardService(db_manager)

    # Create M5 AI-assisted unresolved finding in source engagement
    with db_manager.session_scope() as session:
        matrix_repo = AuditMatrixRepository(session)
        ai_finding = AuditFinding(
            engagement_id=source_eng.id,
            title="Unreconciled GST Input Tax Credit Variance",
            description="AI detected ITC mismatch against GSTR-2B.",
            severity=RiskSeverityEnum.HIGH,
            status=FindingStatusEnum.OPEN,
            amount_paise=25000000,
            source=FindingSourceEnum.AI,
            is_ai_generated=True,
        )
        matrix_repo.add_finding(ai_finding)

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=source_eng.id,
            index_reference="WP-FIN-01",
            title="GST WP",
            area="Taxation",
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
            title="Report 2024-25",
            generated_by="Auditor",
        )
    )
    report_svc.approve_report(ApproveReportDTO(report_id=rep.id, approved_by="Audit Partner", approver_role="Partner"))

    arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=source_eng.id,
            sealed_by="Audit Partner",
            report_date="2025-03-31",
            output_dir=str(tmp_path / "archives"),
        )
    )

    return source_eng, ai_finding, rf_svc, db_manager


def test_carried_findings_preserve_ai_badge_and_provenance(setup_findings_env) -> None:
    """Verify carried-forward findings maintain link to prior finding and preserve M5 AI badges."""
    source_eng, ai_finding, rf_svc, db_manager = setup_findings_env

    new_eng = rf_svc.roll_forward_engagement(
        ExecuteRollForwardDTO(
            source_engagement_id=source_eng.id,
            target_financial_year="2025-26",
            performed_by="Senior Auditor",
            carry_findings=True,
        )
    )

    with db_manager.session_scope() as session:
        matrix_repo = AuditMatrixRepository(session)
        new_findings = matrix_repo.list_findings_for_engagement(new_eng.id)

        assert len(new_findings) == 1
        carried = new_findings[0]

        assert carried.engagement_id == new_eng.id
        assert carried.prior_engagement_finding_id == ai_finding.id
        assert carried.is_ai_generated is True
        assert carried.source == FindingSourceEnum.AI
        assert "carried from FY 2024-25" in carried.title
