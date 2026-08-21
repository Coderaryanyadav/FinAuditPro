"""Firm repository for SQLite persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.entities import Firm
from finauditpro.infrastructure.persistence.models import FirmModel


class FirmRepository:
    """Repository managing Firm persistence operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: FirmModel) -> Firm:
        return Firm(
            id=model.id,
            name=model.name,
            registration_number=model.registration_number,
            pan=model.pan,
            gstin=model.gstin,
            address=model.address,
            phone=model.phone,
            email=model.email,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add(self, firm: Firm) -> Firm:
        model = FirmModel(
            id=firm.id,
            name=firm.name,
            registration_number=firm.registration_number,
            pan=firm.pan,
            gstin=firm.gstin,
            address=firm.address,
            phone=firm.phone,
            email=firm.email,
            created_at=firm.created_at,
            updated_at=firm.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get_by_id(self, firm_id: str) -> Firm | None:
        model = self.session.get(FirmModel, firm_id)
        return self._to_entity(model) if model else None

    def get_by_name(self, name: str) -> Firm | None:
        stmt = select(FirmModel).where(FirmModel.name == name)
        model = self.session.scalars(stmt).first()
        return self._to_entity(model) if model else None

    def list_all(self) -> list[Firm]:
        stmt = select(FirmModel).order_by(FirmModel.name.asc())
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def update(self, firm: Firm) -> Firm:
        model = self.session.get(FirmModel, firm.id)
        if not model:
            raise ValueError(f"Firm with ID '{firm.id}' does not exist.")
        model.name = firm.name
        model.registration_number = firm.registration_number
        model.pan = firm.pan
        model.gstin = firm.gstin
        model.address = firm.address
        model.phone = firm.phone
        model.email = firm.email
        model.updated_at = firm.updated_at
        self.session.flush()
        return self._to_entity(model)

    def delete(self, firm_id: str) -> bool:
        model = self.session.get(FirmModel, firm_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
