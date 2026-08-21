"""Evidence link repository for connecting documents and pages to audit work items."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.document_entities import EvidenceLink
from finauditpro.infrastructure.persistence.models import EvidenceLinkModel


class EvidenceRepository:
    """Repository managing EvidenceLink persistence for traceability across audit work papers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: EvidenceLinkModel) -> EvidenceLink:
        return EvidenceLink(
            id=model.id,
            engagement_id=model.engagement_id,
            document_id=model.document_id,
            page_number=model.page_number,
            target_type=model.target_type,
            target_id=model.target_id,
            title=model.title,
            snippet=model.snippet,
            created_at=model.created_at,
        )

    def add_link(self, link: EvidenceLink) -> EvidenceLink:
        model = EvidenceLinkModel(
            id=link.id,
            engagement_id=link.engagement_id,
            document_id=link.document_id,
            page_number=link.page_number,
            target_type=link.target_type,
            target_id=link.target_id,
            title=link.title,
            snippet=link.snippet,
            created_at=link.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def list_links_by_engagement(self, engagement_id: str) -> list[EvidenceLink]:
        stmt = (
            select(EvidenceLinkModel)
            .where(EvidenceLinkModel.engagement_id == engagement_id)
            .order_by(EvidenceLinkModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def list_links_by_document(self, document_id: str) -> list[EvidenceLink]:
        stmt = (
            select(EvidenceLinkModel)
            .where(EvidenceLinkModel.document_id == document_id)
            .order_by(EvidenceLinkModel.page_number.asc(), EvidenceLinkModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def delete_link(self, link_id: str) -> bool:
        model = self.session.get(EvidenceLinkModel, link_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
