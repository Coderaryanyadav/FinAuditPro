"""Firm application service."""

from finauditpro.application.dtos import CreateFirmDTO, UpdateFirmDTO
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent, Firm
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository, FirmRepository


class FirmService:
    """Service handling audit firm operations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_firm(self, dto: CreateFirmDTO) -> Firm:
        firm = Firm(
            name=dto.name,
            registration_number=dto.registration_number,
            pan=dto.pan,
            gstin=dto.gstin,
            address=dto.address,
            phone=dto.phone,
            email=dto.email,
        )
        with self.db_manager.session_scope() as session:
            repo = FirmRepository(session)
            created_firm = repo.add(firm)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    actor="System",
                    action="Firm Created",
                    details=f"Created firm '{created_firm.name}' (ID: {created_firm.id})",
                )
            )

        return created_firm

    def get_firm(self, firm_id: str) -> Firm:
        with self.db_manager.session_scope() as session:
            repo = FirmRepository(session)
            firm = repo.get_by_id(firm_id)
            if not firm:
                raise EntityNotFoundError("Firm", firm_id)
            return firm

    get_firm_by_id = get_firm


    def list_firms(self) -> list[Firm]:
        with self.db_manager.session_scope() as session:
            repo = FirmRepository(session)
            return repo.list_all()

    def update_firm(self, firm_id: str, dto: UpdateFirmDTO) -> Firm:
        with self.db_manager.session_scope() as session:
            repo = FirmRepository(session)
            existing = repo.get_by_id(firm_id)
            if not existing:
                raise EntityNotFoundError("Firm", firm_id)

            if dto.name is not None:
                existing.name = dto.name
            if dto.registration_number is not None:
                existing.registration_number = dto.registration_number
            if dto.pan is not None:
                existing.pan = dto.pan
            if dto.gstin is not None:
                existing.gstin = dto.gstin
            if dto.address is not None:
                existing.address = dto.address
            if dto.phone is not None:
                existing.phone = dto.phone
            if dto.email is not None:
                existing.email = dto.email
            existing.updated_at = utc_now()

            updated = repo.update(existing)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    actor="System",
                    action="Firm Updated",
                    details=f"Updated firm '{updated.name}' (ID: {updated.id})",
                )
            )

            return updated
