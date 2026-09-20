"""Application Service managing Compliance Workflows, status transitions, evidence linking, and AI explanation assistance."""

import json
from typing import Any

from finauditpro.domain.compliance_workflow_engine import (
    ComplianceItemDTO,
    ComplianceItemStatusEnum,
    ComplianceWorkflowEngine,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.financial_statement_models import ComplianceItemModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    ClientRepository,
    EngagementRepository,
)


class ComplianceWorkflowService:
    """Service managing compliance workflow items, statutory applicability, status transitions, and AI assistance."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def initialize_compliance_items(self, engagement_id: str) -> list[ComplianceItemDTO]:
        """Deterministically derive and persist compliance items for an engagement based on client entity characteristics."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", engagement_id)

            client_repo = ClientRepository(session)
            client = client_repo.get_by_id(eng.client_id)
            client_name = client.name if client else "Client Entity"
            entity_type = getattr(client, "entity_type", "PRIVATE_LIMITED") or "PRIVATE_LIMITED"

            # Check if items already exist
            existing_models = session.query(ComplianceItemModel).filter(
                ComplianceItemModel.engagement_id == engagement_id
            ).all()

            if existing_models:
                return [self._model_to_dto(m) for m in existing_models]

            # Derive items using deterministic engine
            items = ComplianceWorkflowEngine.determine_compliance_items(
                engagement_id=engagement_id,
                client_name=client_name,
                entity_type=entity_type,
                financial_year=eng.financial_year or "2025-26",
            )

            models = []
            for item in items:
                model = ComplianceItemModel(
                    id=item.id,
                    engagement_id=item.engagement_id,
                    requirement=item.requirement,
                    statutory_head=item.statutory_head,
                    rule_code=item.rule_code,
                    applicable=item.applicable,
                    applicability_reason=item.applicability_reason,
                    due_date=item.due_date,
                    status=item.status.value,
                    evidence_json=json.dumps(item.evidence),
                    owner=item.owner,
                    reviewer=item.reviewer,
                    notes=item.notes,
                )
                models.append(model)

            session.add_all(models)
            session.flush()

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="System",
                    action="Compliance Workflow Initialized",
                    details=f"Initialized {len(items)} statutory compliance items for {client_name}.",
                )
            )

            return [self._model_to_dto(m) for m in models]

    def list_compliance_items(
        self, engagement_id: str, status_filter: str | None = None
    ) -> list[ComplianceItemDTO]:
        """Fetch all compliance items for an engagement."""
        with self.db_manager.session_scope() as session:
            query = session.query(ComplianceItemModel).filter(
                ComplianceItemModel.engagement_id == engagement_id
            )
            if status_filter:
                query = query.filter(ComplianceItemModel.status == status_filter)

            models = query.order_by(ComplianceItemModel.due_date.asc()).all()
            if not models:
                return self.initialize_compliance_items(engagement_id)
            return [self._model_to_dto(m) for m in models]

    def update_item_status(
        self,
        engagement_id: str,
        item_id: str,
        new_status: str | ComplianceItemStatusEnum,
        actor: str = "Auditor",
        notes: str | None = None,
    ) -> ComplianceItemDTO:
        """Execute validated compliance status workflow transition."""
        status_enum = (
            ComplianceItemStatusEnum(str(new_status))
            if isinstance(new_status, str)
            else new_status
        )

        with self.db_manager.session_scope() as session:
            model = session.query(ComplianceItemModel).filter(
                ComplianceItemModel.id == item_id,
                ComplianceItemModel.engagement_id == engagement_id,
            ).first()

            if not model:
                raise EntityNotFoundError("ComplianceItem", item_id)

            curr_status = ComplianceItemStatusEnum(model.status)
            if not ComplianceWorkflowEngine.validate_status_transition(curr_status, status_enum):
                raise ValidationError(
                    f"Invalid Compliance Status Transition: Cannot move from '{curr_status.value}' to '{status_enum.value}'."
                )

            model.status = status_enum.value
            if notes is not None:
                model.notes = notes.strip()

            session.flush()

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor=actor,
                    action="Compliance Item Status Updated",
                    details=f"Item '{model.requirement}' moved to status '{status_enum.value}'.",
                )
            )

            return self._model_to_dto(model)

    def attach_evidence_to_item(
        self, engagement_id: str, item_id: str, evidence_ref: str
    ) -> ComplianceItemDTO:
        """Attach evidence document / reference to a compliance item."""
        with self.db_manager.session_scope() as session:
            model = session.query(ComplianceItemModel).filter(
                ComplianceItemModel.id == item_id,
                ComplianceItemModel.engagement_id == engagement_id,
            ).first()

            if not model:
                raise EntityNotFoundError("ComplianceItem", item_id)

            ev_list = json.loads(model.evidence_json) if model.evidence_json else []
            if evidence_ref not in ev_list:
                ev_list.append(evidence_ref)
                model.evidence_json = json.dumps(ev_list)
                session.flush()

            return self._model_to_dto(model)

    def explain_compliance_with_ai(
        self,
        item_dto: ComplianceItemDTO,
        prompt_kind: str = "meaning",  # "meaning", "evidence", or "incomplete"
        ai_service: Any = None,
    ) -> str:
        """Provide AI natural language explanation for statutory meaning, supporting evidence, or incompleteness rationale."""
        if ai_service is not None:
            try:
                question_text = (
                    "What does this requirement mean?"
                    if prompt_kind == "meaning"
                    else (
                        "What documents support this requirement?"
                        if prompt_kind == "evidence"
                        else "Why is this compliance item incomplete?"
                    )
                )
                prompt = (
                    f"Statutory Requirement: {item_dto.requirement} ({item_dto.statutory_head})\n"
                    f"Due Date: {item_dto.due_date} | Status: {item_dto.status.value}\n"
                    f"Applicability: {item_dto.applicability_reason}\n"
                    f"Question: {question_text}"
                )
                ai_resp = ai_service.ask_ai(prompt)
                if ai_resp:
                    return str(ai_resp)
            except Exception:
                pass

        # Deterministic prompt synthesis fallback
        if prompt_kind == "meaning":
            return (
                f"Statutory Requirement Explanation ({item_dto.requirement}):\n"
                f"• Governing Authority: {item_dto.statutory_head}\n"
                f"• Statutory Obligation: {item_dto.applicability_reason}\n"
                f"• Statutory Deadline: {item_dto.due_date} (Note: Statutory deadlines are set by law and cannot be altered by AI)."
            )
        elif prompt_kind == "evidence":
            return (
                f"Recommended Audit Evidence for {item_dto.requirement}:\n"
                f"• Board & Shareholder Resolutions approving compliance action.\n"
                f"• Statutory Returns (AOC-4, MGT-7, Form 3CD, GSTR-9) filed with Portal Ack.\n"
                f"• Payment Challans, Bank Debit Advices, and Working Papers verified by auditor."
            )
        else:
            evidence_count = len(item_dto.evidence)
            return (
                f"Incompleteness Rationale for {item_dto.requirement}:\n"
                f"• Current Status: {item_dto.status.value} (Target: COMPLETED)\n"
                f"• Evidence Documents Attached: {evidence_count} file(s)\n"
                f"• Action Required: Owner ({item_dto.owner}) must attach required audit evidence and submit for Reviewer ({item_dto.reviewer}) sign-off."
            )

    def _model_to_dto(self, model: ComplianceItemModel) -> ComplianceItemDTO:
        ev_list = json.loads(model.evidence_json) if model.evidence_json else []
        return ComplianceItemDTO(
            id=model.id,
            engagement_id=model.engagement_id,
            requirement=model.requirement,
            statutory_head=model.statutory_head,
            rule_code=model.rule_code,
            applicable=model.applicable,
            applicability_reason=model.applicability_reason,
            due_date=model.due_date,
            status=ComplianceItemStatusEnum(model.status),
            evidence=ev_list,
            owner=model.owner,
            reviewer=model.reviewer,
            notes=model.notes,
        )
