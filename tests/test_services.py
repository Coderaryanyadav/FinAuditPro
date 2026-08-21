"""Integration tests for application service workflows."""

import pytest

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import AuditTypeEnum, EngagementStatusEnum, EntityTypeEnum
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_services.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


def test_full_application_lifecycle_workflow(db_manager: DatabaseManager) -> None:
    firm_service = FirmService(db_manager)
    client_service = ClientService(db_manager)
    engagement_service = EngagementService(db_manager)

    # 1. Create Firm
    firm_dto = CreateFirmDTO(
        name="Global Audit LLP",
        registration_number="123456W",
        pan="AAACG9999F",
    )
    firm = firm_service.create_firm(firm_dto)
    assert firm.id is not None
    assert firm.name == "Global Audit LLP"

    # 2. Create Client
    client_dto = CreateClientDTO(
        firm_id=firm.id,
        name="Tata Power Solar Ltd",
        entity_type=EntityTypeEnum.PUBLIC_LTD,
        pan="AAACT1111A",
    )
    client = client_service.create_client(client_dto)
    assert client.id is not None
    assert client.firm_id == firm.id

    # 3. Create Engagement
    eng_dto = CreateEngagementDTO(
        firm_id=firm.id,
        client_id=client.id,
        financial_year="2025-26",
        audit_type=AuditTypeEnum.STATUTORY_AUDIT,
        status=EngagementStatusEnum.PLANNING,
        assigned_team=["Lead Partner", "Audit Manager"],
    )
    engagement = engagement_service.create_engagement(eng_dto)
    assert engagement.id is not None
    assert engagement.client_id == client.id

    # 4. Check Dashboard Summary
    summary = engagement_service.get_dashboard_summary(firm_id=firm.id)
    assert summary.total_clients == 1
    assert summary.active_engagements == 1
    assert summary.completed_engagements == 0
    assert len(summary.recent_activities) >= 3


def test_service_error_handling(db_manager: DatabaseManager) -> None:
    client_service = ClientService(db_manager)
    engagement_service = EngagementService(db_manager)

    with pytest.raises(EntityNotFoundError):
        client_service.create_client(CreateClientDTO(firm_id="non-existent", name="Fail Client"))

    with pytest.raises(EntityNotFoundError):
        engagement_service.create_engagement(
            CreateEngagementDTO(
                firm_id="non-existent-firm",
                client_id="non-existent-client",
                financial_year="2025-26",
            )
        )
