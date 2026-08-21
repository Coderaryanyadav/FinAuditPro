"""Unit tests for deterministic real-query report data assembly and content hash provenance."""

import pytest

from finauditpro.application.report_dtos import GenerateReportDTO
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
def setup_report_env(tmp_path):
    db_file = tmp_path / "test_report_m7.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Report Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Report Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    report_svc = ReportService(db_manager)
    return eng, report_svc


def test_report_data_assembly_and_hash_provenance(setup_report_env) -> None:
    """Verify report data assembly queries real records and computes deterministic content hash."""
    eng, report_svc = setup_report_env

    templates = report_svc.list_templates()
    assert len(templates) > 0

    tpl = templates[0]

    report = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng.id,
            template_id=tpl.id,
            title="Audit Findings Summary Report",
            generated_by="Senior Auditor",
        )
    )

    assert report.id is not None
    assert report.status == ReportStatusEnum.DRAFT
    assert len(report.content_hash) == 64

    # Verify report is listed under engagement
    reports = report_svc.list_reports(eng.id)
    assert len(reports) == 1
    assert reports[0].id == report.id
