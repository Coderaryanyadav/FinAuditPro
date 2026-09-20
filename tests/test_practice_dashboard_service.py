"""Unit tests for PracticeDashboardService aggregation and DTO generation."""

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.practice_dashboard_service import PracticeDashboardService
from finauditpro.infrastructure.persistence.database import DatabaseManager


def test_practice_dashboard_service_empty_db(tmp_path) -> None:
    """Test PracticeDashboardService returns safe empty state DTOs when database is fresh."""
    db_path = tmp_path / "test_empty_dash.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    service = PracticeDashboardService(db_manager)
    summary = service.get_practice_summary()

    assert summary is not None
    assert summary.firm_name == "CA Practice"
    assert summary.total_clients == 0
    assert summary.active_engagements == 0
    assert summary.completed_audits == 0
    assert len(summary.attention_items) == 0
    assert len(summary.active_clients) == 0


def test_practice_dashboard_service_with_clients_and_engagements(tmp_path) -> None:
    """Test PracticeDashboardService aggregates client metrics and active engagement status."""
    db_path = tmp_path / "test_dash_populated.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Enterprise CA Firm"))
    c1 = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha Ltd", industry="Manufacturing"))
    c2 = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta Inc", industry="IT Services"))

    eng1 = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=c1.id, financial_year="2025-26", audit_type="Statutory Audit")
    )
    eng2 = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=c2.id, financial_year="2025-26", audit_type="Tax Audit")
    )

    service = PracticeDashboardService(db_manager)
    summary = service.get_practice_summary(firm_id=firm.id)

    assert summary.firm_name == "Enterprise CA Firm"
    assert summary.total_clients == 2
    assert summary.active_engagements == 2
    assert len(summary.active_clients) == 2

    c_names = [ac.client_name for ac in summary.active_clients]
    assert "Client Alpha Ltd" in c_names
    assert "Client Beta Inc" in c_names
