"""Repository for Audit Query persistence."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.clock import utc_now
from finauditpro.domain.pbc_and_query_entities import AuditQuery, AuditQueryStatusEnum
from finauditpro.infrastructure.persistence.pbc_and_query_models import AuditQueryModel


class AuditQueryRepository:
    """Repository handling CRUD and queries for audit queries."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, m: AuditQueryModel) -> AuditQuery:
        try:
            status = AuditQueryStatusEnum(m.status)
        except ValueError:
            status = AuditQueryStatusEnum.DRAFT

        return AuditQuery(
            id=m.id,
            engagement_id=m.engagement_id,
            query_text=m.query_text,
            audit_area=m.audit_area,
            working_paper_id=m.working_paper_id,
            procedure_id=m.procedure_id,
            assigned_to=m.assigned_to,
            client_contact=m.client_contact,
            evidence_requested=m.evidence_requested,
            due_date=m.due_date,
            status=status,
            response_text=m.response_text,
            resolution_notes=m.resolution_notes,
            reviewer_id=m.reviewer_id,
            escalated_finding_id=m.escalated_finding_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def add(self, entity: AuditQuery) -> AuditQuery:
        if not entity.id:
            entity.id = str(uuid4())
        model = AuditQueryModel(
            id=entity.id,
            engagement_id=entity.engagement_id,
            query_text=entity.query_text,
            audit_area=entity.audit_area,
            working_paper_id=entity.working_paper_id,
            procedure_id=entity.procedure_id,
            assigned_to=entity.assigned_to,
            client_contact=entity.client_contact,
            evidence_requested=entity.evidence_requested,
            due_date=entity.due_date,
            status=entity.status.value,
            response_text=entity.response_text,
            resolution_notes=entity.resolution_notes,
            reviewer_id=entity.reviewer_id,
            escalated_finding_id=entity.escalated_finding_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get(self, query_id: str) -> AuditQuery | None:
        stmt = select(AuditQueryModel).where(AuditQueryModel.id == query_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_by_engagement(self, engagement_id: str) -> list[AuditQuery]:
        stmt = (
            select(AuditQueryModel)
            .where(AuditQueryModel.engagement_id == engagement_id)
            .order_by(AuditQueryModel.created_at.asc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def list_by_working_paper(self, working_paper_id: str) -> list[AuditQuery]:
        stmt = (
            select(AuditQueryModel)
            .where(AuditQueryModel.working_paper_id == working_paper_id)
            .order_by(AuditQueryModel.created_at.asc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def update(self, entity: AuditQuery) -> AuditQuery:
        stmt = select(AuditQueryModel).where(AuditQueryModel.id == entity.id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            raise ValueError(f"AuditQuery '{entity.id}' not found.")

        model.query_text = entity.query_text
        model.audit_area = entity.audit_area
        model.working_paper_id = entity.working_paper_id
        model.procedure_id = entity.procedure_id
        model.assigned_to = entity.assigned_to
        model.client_contact = entity.client_contact
        model.evidence_requested = entity.evidence_requested
        model.due_date = entity.due_date
        model.status = entity.status.value
        model.response_text = entity.response_text
        model.resolution_notes = entity.resolution_notes
        model.reviewer_id = entity.reviewer_id
        model.escalated_finding_id = entity.escalated_finding_id
        model.updated_at = utc_now()

        self.session.flush()
        return self._to_entity(model)

    def delete(self, query_id: str) -> bool:
        stmt = select(AuditQueryModel).where(AuditQueryModel.id == query_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
