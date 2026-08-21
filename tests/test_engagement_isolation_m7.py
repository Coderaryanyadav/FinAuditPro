"""Unit tests for multi-tenant engagement isolation of reports and export artifacts."""

import pytest

from finauditpro.application.report_dtos import GenerateReportDTO
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_isolation_env(tmp_path):
    db_file = tmp_path / "test_iso_m7.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Iso Firm M7"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha M7"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta M7"))

    eng_a = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26")
    )
    eng_b = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26")
    )

    report_svc = ReportService(db_manager)
    return eng_a, eng_b, report_svc


def test_engagement_isolation_reports(setup_isolation_env) -> None:
    """Verify reports generated under Engagement A never surface under Engagement B."""
    eng_a, eng_b, report_svc = setup_isolation_env

    tpls = report_svc.list_templates()
    report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng_a.id,
            template_id=tpls[0].id,
            title="Alpha Report",
            generated_by="Auditor Alpha",
        )
    )

    # Engagement B returns 0 reports
    reports_b = report_svc.list_reports(eng_b.id)
    assert len(reports_b) == 0

    # Engagement A returns exactly 1 report
    reports_a = report_svc.list_reports(eng_a.id)
    assert len(reports_a) == 1
    assert reports_a[0].title == "Alpha Report"
