"""Unit tests for report approval workflow and watermark removal."""

from pathlib import Path

import pytest

from finauditpro.application.report_dtos import ApproveReportDTO, GenerateReportDTO
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.domain.report_entities import ReportStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_approval_env(tmp_path):
    db_file = tmp_path / "test_appr_m7.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Appr Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Appr Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    report_svc = ReportService(db_manager)
    return eng, report_svc


def test_report_approval_workflow_and_watermark_removal(setup_approval_env) -> None:
    """Verify report transitions to Approved and re-rendered PDF removes DRAFT watermark."""
    eng, report_svc = setup_approval_env

    tpls = report_svc.list_templates()
    report = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng.id,
            template_id=tpls[0].id,
            title="Approval Workflow Test Report",
            generated_by="Senior Auditor",
        )
    )

    assert report.status == ReportStatusEnum.DRAFT

    # Approve report
    approved_report = report_svc.approve_report(
        ApproveReportDTO(
            report_id=report.id,
            approved_by="Audit Partner",
            approver_role="Partner",
        )
    )

    assert approved_report.status == ReportStatusEnum.APPROVED
    assert approved_report.approved_by == "Audit Partner"

    # Verify re-rendered PDF has no DRAFT watermark string
    pdf_path = (
        Path(str(report_svc.db_manager.engine.url.database)).parent
        / "reports"
        / eng.id
        / f"report_{report.id}.pdf"
    )
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    assert "DRAFT — NOT FOR ISSUANCE".encode() not in pdf_bytes
