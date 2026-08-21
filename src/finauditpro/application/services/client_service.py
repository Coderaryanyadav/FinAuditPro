"""Client application service."""

from finauditpro.application.dtos import CreateClientDTO, UpdateClientDTO
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent, Client
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    ClientRepository,
    FirmRepository,
)


class ClientService:
    """Service handling client operations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_client(self, dto: CreateClientDTO) -> Client:
        with self.db_manager.session_scope() as session:
            firm_repo = FirmRepository(session)
            if not firm_repo.get_by_id(dto.firm_id):
                raise EntityNotFoundError("Firm", dto.firm_id)

            client = Client(
                firm_id=dto.firm_id,
                name=dto.name,
                entity_type=dto.entity_type,
                pan=dto.pan,
                gstin=dto.gstin,
                registered_address=dto.registered_address,
                industry=dto.industry,
                contact_person=dto.contact_person,
                contact_email=dto.contact_email,
            )

            client_repo = ClientRepository(session)
            created_client = client_repo.add(client)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    actor="System",
                    action="Client Created",
                    details=f"Created client '{created_client.name}' for firm '{dto.firm_id}'",
                )
            )

            return created_client

    def get_client(self, client_id: str) -> Client:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            client = repo.get_by_id(client_id)
            if not client:
                raise EntityNotFoundError("Client", client_id)
            return client

    def list_clients_for_firm(self, firm_id: str) -> list[Client]:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            return repo.list_by_firm(firm_id)

    def list_all_clients(self) -> list[Client]:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            return repo.list_all()

    list_clients = list_all_clients

    def update_client(self, client_id: str, dto: UpdateClientDTO) -> Client:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            existing = repo.get_by_id(client_id)
            if not existing:
                raise EntityNotFoundError("Client", client_id)

            if dto.name is not None:
                existing.name = dto.name
            if dto.entity_type is not None:
                existing.entity_type = dto.entity_type
            if dto.pan is not None:
                existing.pan = dto.pan
            if dto.gstin is not None:
                existing.gstin = dto.gstin
            if dto.registered_address is not None:
                existing.registered_address = dto.registered_address
            if dto.industry is not None:
                existing.industry = dto.industry
            if dto.contact_person is not None:
                existing.contact_person = dto.contact_person
            if dto.contact_email is not None:
                existing.contact_email = dto.contact_email
            existing.updated_at = utc_now()

            updated = repo.update(existing)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    actor="System",
                    action="Client Updated",
                    details=f"Updated client '{updated.name}' (ID: {updated.id})",
                )
            )

            return updated
