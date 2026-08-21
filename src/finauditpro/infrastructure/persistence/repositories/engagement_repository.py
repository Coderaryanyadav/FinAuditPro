"""Engagement repository for SQLite persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.entities import AuditTypeEnum, Engagement, EngagementStatusEnum
from finauditpro.infrastructure.persistence.models import EngagementModel


class EngagementRepository:
    """Repository managing Engagement persistence operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: EngagementModel) -> Engagement:
        return Engagement(
            id=model.id,
            firm_id=model.firm_id,
            client_id=model.client_id,
            financial_year=model.financial_year,
            audit_type=AuditTypeEnum(model.audit_type),
            status=EngagementStatusEnum(model.status),
            prior_engagement_id=model.prior_engagement_id,
            assigned_team=model.assigned_team or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add(self, engagement: Engagement) -> Engagement:
        model = EngagementModel(
            id=engagement.id,
            firm_id=engagement.firm_id,
            client_id=engagement.client_id,
            financial_year=engagement.financial_year,
            audit_type=engagement.audit_type.value,
            status=engagement.status.value,
            prior_engagement_id=engagement.prior_engagement_id,
            assigned_team=engagement.assigned_team,
            created_at=engagement.created_at,
            updated_at=engagement.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get_by_id(self, engagement_id: str) -> Engagement | None:
        model = self.session.get(EngagementModel, engagement_id)
        return self._to_entity(model) if model else None

    def list_by_client(self, client_id: str) -> list[Engagement]:
        stmt = (
            select(EngagementModel)
            .where(EngagementModel.client_id == client_id)
            .order_by(EngagementModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def list_by_firm(self, firm_id: str) -> list[Engagement]:
        stmt = (
            select(EngagementModel)
            .where(EngagementModel.firm_id == firm_id)
            .order_by(EngagementModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def list_all(self) -> list[Engagement]:
        stmt = select(EngagementModel).order_by(EngagementModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def update(self, engagement: Engagement) -> Engagement:
        model = self.session.get(EngagementModel, engagement.id)
        if not model:
            raise ValueError(f"Engagement '{engagement.id}' does not exist.")
        model.financial_year = engagement.financial_year
        model.audit_type = engagement.audit_type.value
        model.status = engagement.status.value
        model.prior_engagement_id = engagement.prior_engagement_id
        model.assigned_team = engagement.assigned_team
        model.updated_at = engagement.updated_at
        self.session.flush()
        return self._to_entity(model)

    def delete(self, engagement_id: str) -> bool:
        model = self.session.get(EngagementModel, engagement_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
