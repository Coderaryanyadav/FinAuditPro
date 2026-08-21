"""Integration tests for persistence and database repositories across session restarts."""

import pytest

from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    EntityTypeEnum,
    Firm,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_finauditpro.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


def test_firm_repository_crud(db_manager: DatabaseManager) -> None:
    firm = Firm(name="Test Audit Firm", registration_number="FRN999")

    # Add
    with db_manager.session_scope() as session:
        repo = FirmRepository(session)
        created = repo.add(firm)
        assert created.id == firm.id

    # Retrieve across restart / new session
    with db_manager.session_scope() as session:
        repo = FirmRepository(session)
        retrieved = repo.get_by_id(firm.id)
        assert retrieved is not None
        assert retrieved.name == "Test Audit Firm"
        assert retrieved.registration_number == "FRN999"

    # Update
    firm.name = "Updated Audit Firm"
    with db_manager.session_scope() as session:
        repo = FirmRepository(session)
        updated = repo.update(firm)
        assert updated.name == "Updated Audit Firm"

    # List
    with db_manager.session_scope() as session:
        repo = FirmRepository(session)
        firms = repo.list_all()
        assert len(firms) == 1
        assert firms[0].name == "Updated Audit Firm"


def test_client_and_engagement_persistence(db_manager: DatabaseManager) -> None:
    firm = Firm(name="Primary Firm")
    client = Client(firm_id=firm.id, name="Test Client Ltd", entity_type=EntityTypeEnum.PVT_LTD)

    with db_manager.session_scope() as session:
        FirmRepository(session).add(firm)
        ClientRepository(session).add(client)

    engagement = Engagement(
        firm_id=firm.id,
        client_id=client.id,
        financial_year="2025-26",
        audit_type=AuditTypeEnum.STATUTORY_AUDIT,
        status=EngagementStatusEnum.PLANNING,
    )

    with db_manager.session_scope() as session:
        EngagementRepository(session).add(engagement)

    # Verify complete graph in separate session
    with db_manager.session_scope() as session:
        f = FirmRepository(session).get_by_id(firm.id)
        c = ClientRepository(session).get_by_id(client.id)
        e = EngagementRepository(session).get_by_id(engagement.id)

        assert f is not None and f.name == "Primary Firm"
        assert c is not None and c.name == "Test Client Ltd"
        assert e is not None and e.financial_year == "2025-26"
