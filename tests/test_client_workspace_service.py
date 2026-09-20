"""Unit tests for ClientWorkspaceService data aggregation and metrics."""

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.client_workspace_service import ClientWorkspaceService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.infrastructure.persistence.database import DatabaseManager


def test_client_workspace_service_aggregation(tmp_path) -> None:
    """Test ClientWorkspaceService queries client details, active FY, and engagement list correctly."""
    db_path = tmp_path / "test_client_ws.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    workspace_svc = ClientWorkspaceService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Workspace Test Firm"))
    client = client_svc.create_client(
        CreateClientDTO(
            firm_id=firm.id,
            name="Reliance Energy Pvt Ltd",
            entity_type="Private Limited Company",
            pan="ABCDE1234F",
            gstin="27ABCDE1234F1Z5",
            industry="Energy & Power",
        )
    )

    eng1 = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2024-25", audit_type="Statutory Audit")
    )
    eng2 = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26", audit_type="Statutory Audit")
    )

    summary = workspace_svc.get_client_workspace_summary(client.id)

    assert summary is not None
    assert summary.header.client_name == "Reliance Energy Pvt Ltd"
    assert summary.header.pan == "ABCDE1234F"
    assert summary.header.gstin == "27ABCDE1234F1Z5"
    assert summary.header.active_fy == "2025-26"
    assert len(summary.engagements) == 2
