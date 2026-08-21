"""Unit tests for multi-tenant engagement isolation of Working Papers and Review Notes."""

import pytest

from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_isolation_env(tmp_path):
    db_file = tmp_path / "test_isolation_m6.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Isolation Firm M6"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha M6"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta M6"))

    eng_a = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26")
    )
    eng_b = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26")
    )

    wp_svc = WorkingPaperService(db_manager)
    return eng_a, eng_b, wp_svc


def test_engagement_isolation_working_papers(setup_isolation_env) -> None:
    """Verify Working Papers of Engagement A never surface under Engagement B."""
    eng_a, eng_b, wp_svc = setup_isolation_env

    # Create WP under Engagement A
    wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-ALPHA-01",
            title="Alpha Working Paper",
            area="Revenue",
            preparer_id="Auditor Alpha",
        )
    )

    # Verify Engagement B returns 0 working papers
    wps_b = wp_svc.list_working_papers(eng_b.id)
    assert len(wps_b) == 0

    # Verify Engagement A returns exactly 1 working paper
    wps_a = wp_svc.list_working_papers(eng_a.id)
    assert len(wps_a) == 1
    assert wps_a[0].index_reference == "WP-ALPHA-01"
