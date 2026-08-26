"""Application service managing Client Document Request (PBC) workflows."""

from uuid import uuid4

from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.pbc_and_query_entities import (
    DEFAULT_STATUTORY_PBC_TEMPLATES,
    DocumentRequest,
    DocumentRequestStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import (
    AuditEventRepository,
)
from finauditpro.infrastructure.persistence.repositories.document_request_repository import (
    DocumentRequestRepository,
)


class DocumentRequestService:
    """Orchestrates creation, tracking, status transitions, and attachments for PBC requests."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def seed_default_pbc_package(self, engagement_id: str, actor: str = "Auditor") -> list[DocumentRequest]:
        """Seed standard ICAI statutory PBC document requests for an engagement."""
        created_requests: list[DocumentRequest] = []
        with self.db_manager.session_scope() as session:
            repo = DocumentRequestRepository(session)
            existing = repo.list_by_engagement(engagement_id)
            if existing:
                return existing

            for tpl in DEFAULT_STATUTORY_PBC_TEMPLATES:
                req = DocumentRequest(
                    id=str(uuid4()),
                    engagement_id=engagement_id,
                    title=tpl["title"],
                    description=tpl["description"],
                    period=tpl.get("period", "Full Year"),
                    status=DocumentRequestStatusEnum.REQUESTED,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                created_requests.append(repo.add(req))

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor=actor,
                    action="PBC Package Seeded",
                    details=f"Initialized {len(created_requests)} standard ICAI statutory PBC document requests.",
                )
            )
        return created_requests

    def create_request(
        self,
        engagement_id: str,
        title: str,
        description: str,
        period: str = "FY 2025-26",
        contact_name: str | None = None,
        contact_email: str | None = None,
        due_date: str | None = None,
        actor: str = "Auditor",
    ) -> DocumentRequest:
        with self.db_manager.session_scope() as session:
            repo = DocumentRequestRepository(session)
            req = DocumentRequest(
                id=str(uuid4()),
                engagement_id=engagement_id,
                title=title,
                description=description,
                period=period,
                contact_name=contact_name,
                contact_email=contact_email,
                due_date=due_date,
                status=DocumentRequestStatusEnum.REQUESTED,
            )
            saved = repo.add(req)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor=actor,
                    action="Document Requested",
                    details=f"Created client document request: '{title}' (Due: {due_date or 'N/A'}).",
                )
            )
            return saved

    def list_requests(self, engagement_id: str) -> list[DocumentRequest]:
        with self.db_manager.session_scope() as session:
            return DocumentRequestRepository(session).list_by_engagement(engagement_id)

    def get_request(self, request_id: str) -> DocumentRequest | None:
        with self.db_manager.session_scope() as session:
            return DocumentRequestRepository(session).get(request_id)

    def update_status(
        self,
        request_id: str,
        target_status: DocumentRequestStatusEnum | str,
        reviewer_notes: str | None = None,
        actor: str = "Auditor",
    ) -> DocumentRequest:
        with self.db_manager.session_scope() as session:
            repo = DocumentRequestRepository(session)
            req = repo.get(request_id)
            if not req:
                raise ValueError(f"PBC Request '{request_id}' not found.")

            if isinstance(target_status, DocumentRequestStatusEnum):
                status_enum = target_status
            else:
                try:
                    status_enum = DocumentRequestStatusEnum(target_status)
                except ValueError:
                    status_enum = DocumentRequestStatusEnum[target_status] if str(target_status) in DocumentRequestStatusEnum.__members__ else DocumentRequestStatusEnum.REQUESTED

            req.transition_to(status_enum)
            if reviewer_notes:
                req.reviewer_notes = reviewer_notes
            saved = repo.update(req)

            status_val = getattr(status_enum, "value", str(status_enum))
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=req.engagement_id,
                    actor=actor,
                    action="Document Request Status Updated",
                    details=f"Request '{req.title}' moved to '{status_val}'. Notes: {reviewer_notes or 'None'}",
                )
            )
            return saved

    def attach_document(self, request_id: str, document_id: str, actor: str = "Auditor") -> DocumentRequest:
        with self.db_manager.session_scope() as session:
            repo = DocumentRequestRepository(session)
            req = repo.get(request_id)
            if not req:
                raise ValueError(f"PBC Request '{request_id}' not found.")

            if document_id not in req.uploaded_doc_ids:
                req.uploaded_doc_ids.append(document_id)
                if req.status == DocumentRequestStatusEnum.REQUESTED:
                    req.transition_to(DocumentRequestStatusEnum.RECEIVED)
                saved = repo.update(req)
                AuditEventRepository(session).add(
                    AuditEvent(
                        engagement_id=req.engagement_id,
                        actor=actor,
                        action="Document Attached to Request",
                        details=f"Attached document '{document_id[:8]}...' to request '{req.title}'.",
                    )
                )
                return saved
            return req
