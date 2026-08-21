"""Client repository for SQLite persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.entities import Client, EntityTypeEnum
from finauditpro.infrastructure.persistence.models import ClientModel


class ClientRepository:
    """Repository managing Client persistence operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: ClientModel) -> Client:
        return Client(
            id=model.id,
            firm_id=model.firm_id,
            name=model.name,
            entity_type=EntityTypeEnum(model.entity_type),
            pan=model.pan,
            gstin=model.gstin,
            registered_address=model.registered_address,
            industry=model.industry,
            contact_person=model.contact_person,
            contact_email=model.contact_email,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add(self, client: Client) -> Client:
        model = ClientModel(
            id=client.id,
            firm_id=client.firm_id,
            name=client.name,
            entity_type=client.entity_type.value,
            pan=client.pan,
            gstin=client.gstin,
            registered_address=client.registered_address,
            industry=client.industry,
            contact_person=client.contact_person,
            contact_email=client.contact_email,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get_by_id(self, client_id: str) -> Client | None:
        model = self.session.get(ClientModel, client_id)
        return self._to_entity(model) if model else None

    def list_by_firm(self, firm_id: str) -> list[Client]:
        stmt = select(ClientModel).where(ClientModel.firm_id == firm_id).order_by(ClientModel.name.asc())
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def list_all(self) -> list[Client]:
        stmt = select(ClientModel).order_by(ClientModel.name.asc())
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def update(self, client: Client) -> Client:
        model = self.session.get(ClientModel, client.id)
        if not model:
            raise ValueError(f"Client with ID '{client.id}' does not exist.")
        model.name = client.name
        model.entity_type = client.entity_type.value
        model.pan = client.pan
        model.gstin = client.gstin
        model.registered_address = client.registered_address
        model.industry = client.industry
        model.contact_person = client.contact_person
        model.contact_email = client.contact_email
        model.updated_at = client.updated_at
        self.session.flush()
        return self._to_entity(model)

    def delete(self, client_id: str) -> bool:
        model = self.session.get(ClientModel, client_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
