"""Repository for Client Document Requests (PBC) persistence."""

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.clock import utc_now
from finauditpro.domain.pbc_and_query_entities import DocumentRequest, DocumentRequestStatusEnum
from finauditpro.infrastructure.persistence.pbc_and_query_models import ClientDocumentRequestModel


class DocumentRequestRepository:
    """Repository handling CRUD and queries for client document requests."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, m: ClientDocumentRequestModel) -> DocumentRequest:
        try:
            status = DocumentRequestStatusEnum(m.status)
        except ValueError:
            status = DocumentRequestStatusEnum.REQUESTED
        try:
            uploaded_ids = json.loads(m.uploaded_doc_ids_json) if m.uploaded_doc_ids_json else []
        except Exception:
            uploaded_ids = []

        return DocumentRequest(
            id=m.id,
            engagement_id=m.engagement_id,
            title=m.title,
            description=m.description,
            period=m.period,
            contact_name=m.contact_name,
            contact_email=m.contact_email,
            due_date=m.due_date,
            status=status,
            uploaded_doc_ids=uploaded_ids,
            reviewer_notes=m.reviewer_notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def add(self, entity: DocumentRequest) -> DocumentRequest:
        if not entity.id:
            entity.id = str(uuid4())
        model = ClientDocumentRequestModel(
            id=entity.id,
            engagement_id=entity.engagement_id,
            title=entity.title,
            description=entity.description,
            period=entity.period,
            contact_name=entity.contact_name,
            contact_email=entity.contact_email,
            due_date=entity.due_date,
            status=entity.status.value,
            uploaded_doc_ids_json=json.dumps(entity.uploaded_doc_ids),
            reviewer_notes=entity.reviewer_notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get(self, request_id: str) -> DocumentRequest | None:
        stmt = select(ClientDocumentRequestModel).where(ClientDocumentRequestModel.id == request_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_by_engagement(self, engagement_id: str) -> list[DocumentRequest]:
        stmt = (
            select(ClientDocumentRequestModel)
            .where(ClientDocumentRequestModel.engagement_id == engagement_id)
            .order_by(ClientDocumentRequestModel.created_at.asc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def update(self, entity: DocumentRequest) -> DocumentRequest:
        stmt = select(ClientDocumentRequestModel).where(ClientDocumentRequestModel.id == entity.id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            raise ValueError(f"DocumentRequest '{entity.id}' not found.")

        model.title = entity.title
        model.description = entity.description
        model.period = entity.period
        model.contact_name = entity.contact_name
        model.contact_email = entity.contact_email
        model.due_date = entity.due_date
        model.status = entity.status.value
        model.uploaded_doc_ids_json = json.dumps(entity.uploaded_doc_ids)
        model.reviewer_notes = entity.reviewer_notes
        model.updated_at = utc_now()

        self.session.flush()
        return self._to_entity(model)

    def delete(self, request_id: str) -> bool:
        stmt = select(ClientDocumentRequestModel).where(ClientDocumentRequestModel.id == request_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False


class ExternalConfirmationRepository:
    """Repository handling CRUD and queries for SA 505 third-party external confirmations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, m: Any) -> Any:
        from finauditpro.domain.pbc_and_query_entities import (
            ConfirmationStatusEnum,
            ConfirmationTypeEnum,
            ExternalConfirmation,
        )

        try:
            c_type = ConfirmationTypeEnum(m.confirmation_type)
        except ValueError:
            c_type = ConfirmationTypeEnum.BANK
        try:
            c_status = ConfirmationStatusEnum(m.status)
        except ValueError:
            c_status = ConfirmationStatusEnum.DRAFT

        return ExternalConfirmation(
            id=m.id,
            engagement_id=m.engagement_id,
            confirmation_type=c_type,
            third_party_name=m.third_party_name,
            account_reference=m.account_reference,
            book_balance_paise=m.book_balance_paise,
            as_of_date=m.as_of_date,
            contact_email=m.contact_email,
            contact_address=m.contact_address,
            status=c_status,
            dispatched_date=m.dispatched_date,
            response_date=m.response_date,
            confirmed_balance_paise=m.confirmed_balance_paise,
            discrepancy_paise=m.discrepancy_paise,
            discrepancy_explanation=m.discrepancy_explanation,
            alternative_procedures_note=m.alternative_procedures_note,
            linked_working_paper_id=m.linked_working_paper_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def add(self, entity: Any) -> Any:
        from finauditpro.infrastructure.persistence.pbc_and_query_models import (
            ExternalConfirmationModel,
        )

        if not entity.id:
            entity.id = str(uuid4())
        model = ExternalConfirmationModel(
            id=entity.id,
            engagement_id=entity.engagement_id,
            confirmation_type=entity.confirmation_type.value
            if hasattr(entity.confirmation_type, "value")
            else str(entity.confirmation_type),
            third_party_name=entity.third_party_name,
            account_reference=entity.account_reference,
            book_balance_paise=entity.book_balance_paise,
            as_of_date=entity.as_of_date,
            contact_email=entity.contact_email,
            contact_address=entity.contact_address,
            status=entity.status.value if hasattr(entity.status, "value") else str(entity.status),
            dispatched_date=entity.dispatched_date,
            response_date=entity.response_date,
            confirmed_balance_paise=entity.confirmed_balance_paise,
            discrepancy_paise=entity.discrepancy_paise,
            discrepancy_explanation=entity.discrepancy_explanation,
            alternative_procedures_note=entity.alternative_procedures_note,
            linked_working_paper_id=entity.linked_working_paper_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get(self, confirmation_id: str) -> Any | None:
        from finauditpro.infrastructure.persistence.pbc_and_query_models import (
            ExternalConfirmationModel,
        )

        stmt = select(ExternalConfirmationModel).where(
            ExternalConfirmationModel.id == confirmation_id
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_by_engagement(self, engagement_id: str) -> list[Any]:
        from finauditpro.infrastructure.persistence.pbc_and_query_models import (
            ExternalConfirmationModel,
        )

        stmt = (
            select(ExternalConfirmationModel)
            .where(ExternalConfirmationModel.engagement_id == engagement_id)
            .order_by(ExternalConfirmationModel.created_at.asc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def update(self, entity: Any) -> Any:
        from finauditpro.infrastructure.persistence.pbc_and_query_models import (
            ExternalConfirmationModel,
        )

        stmt = select(ExternalConfirmationModel).where(ExternalConfirmationModel.id == entity.id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            raise ValueError(f"ExternalConfirmation '{entity.id}' not found.")

        model.confirmation_type = (
            entity.confirmation_type.value
            if hasattr(entity.confirmation_type, "value")
            else str(entity.confirmation_type)
        )
        model.third_party_name = entity.third_party_name
        model.account_reference = entity.account_reference
        model.book_balance_paise = entity.book_balance_paise
        model.as_of_date = entity.as_of_date
        model.contact_email = entity.contact_email
        model.contact_address = entity.contact_address
        model.status = (
            entity.status.value if hasattr(entity.status, "value") else str(entity.status)
        )
        model.dispatched_date = entity.dispatched_date
        model.response_date = entity.response_date
        model.confirmed_balance_paise = entity.confirmed_balance_paise
        model.discrepancy_paise = entity.discrepancy_paise
        model.discrepancy_explanation = entity.discrepancy_explanation
        model.alternative_procedures_note = entity.alternative_procedures_note
        model.linked_working_paper_id = entity.linked_working_paper_id
        model.updated_at = utc_now()

        self.session.flush()
        return self._to_entity(model)
