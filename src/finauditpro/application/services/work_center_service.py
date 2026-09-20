"""Application service orchestrating Work Center tasks, multi-section aggregation, and quick actions."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from finauditpro.application.dtos_work import WorkCenterFilterDTO, WorkCenterSummaryDTO, WorkItemDTO
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import AuditFindingModel, EngagementModel
from finauditpro.infrastructure.persistence.pbc_and_query_models import ClientDocumentRequestModel
from finauditpro.infrastructure.persistence.work_models import WorkTaskModel
from finauditpro.infrastructure.persistence.working_paper_models import WorkingPaperModel


class WorkCenterService:
    """Orchestrates CA practice work items, AI task confirmations, and quick actions."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_task(
        self,
        title: str,
        description: str = "",
        client_id: str | None = None,
        engagement_id: str | None = None,
        assignee: str = "Unassigned",
        due_at: str | None = None,
        status: str = "TODO",
        priority: str = "MEDIUM",
        source: str = "MANUAL",
        linked_document: str | None = None,
        linked_workpaper: str | None = None,
        linked_finding: str | None = None,
    ) -> WorkItemDTO:
        """Create a new work task. AI_SUGGESTION source requires human confirmation."""
        task_id = str(uuid.uuid4())
        now_str = datetime.now(UTC).isoformat()
        is_ai = source.upper() == "AI_SUGGESTION"
        is_confirmed = 0 if is_ai else 1

        with self.db_manager.session_scope() as session:
            model = WorkTaskModel(
                id=task_id,
                title=title,
                description=description,
                client_id=client_id,
                engagement_id=engagement_id,
                assignee=assignee,
                created_at=now_str,
                due_at=due_at or "N/A",
                status=status.upper(),
                priority=priority.upper(),
                source=source.upper(),
                linked_document=linked_document,
                linked_workpaper=linked_workpaper,
                linked_finding=linked_finding,
                is_confirmed=is_confirmed,
            )
            session.add(model)
            session.commit()
            return self._task_model_to_dto(session, model)

    def confirm_ai_suggestion(self, task_id: str) -> WorkItemDTO | None:
        """Confirm an AI-suggested task, converting it into an authoritative task."""
        with self.db_manager.session_scope() as session:
            model = session.query(WorkTaskModel).filter(WorkTaskModel.id == task_id).first()
            if not model:
                return None
            model.is_confirmed = 1
            if model.status == "WAITING_REVIEW":
                model.status = "TODO"
            session.commit()
            return self._task_model_to_dto(session, model)

    def update_task_status(self, task_id: str, new_status: str) -> WorkItemDTO | None:
        """Update task status."""
        with self.db_manager.session_scope() as session:
            model = session.query(WorkTaskModel).filter(WorkTaskModel.id == task_id).first()
            if not model:
                return None
            model.status = new_status.upper()
            session.commit()
            return self._task_model_to_dto(session, model)

    def assign_task(self, task_id: str, assignee: str) -> WorkItemDTO | None:
        """Quick action to reassign a task."""
        with self.db_manager.session_scope() as session:
            model = session.query(WorkTaskModel).filter(WorkTaskModel.id == task_id).first()
            if not model:
                return None
            model.assignee = assignee
            session.commit()
            return self._task_model_to_dto(session, model)

    def postpone_task(self, task_id: str, new_due_at: str) -> WorkItemDTO | None:
        """Quick action to postpone task due date."""
        with self.db_manager.session_scope() as session:
            model = session.query(WorkTaskModel).filter(WorkTaskModel.id == task_id).first()
            if not model:
                return None
            model.due_at = new_due_at
            session.commit()
            return self._task_model_to_dto(session, model)

    def get_work_items(self, filter_dto: WorkCenterFilterDTO | None = None) -> list[WorkItemDTO]:
        """Fetch unified work items filtered by section, client, status, priority, assignee."""
        filters = filter_dto or WorkCenterFilterDTO()
        section = filters.section or "Tasks"
        with self.db_manager.session_scope() as session:
            if section == "Compliance":
                return self._fetch_compliance_items(session, filters)
            elif section == "Reconciliations":
                return self._fetch_reconciliation_items(session, filters)
            elif section == "Client Requests":
                return self._fetch_client_requests(session, filters)
            elif section == "Review Notes":
                return self._fetch_review_notes(session, filters)
            elif section == "Audit Actions":
                return self._fetch_audit_actions(session, filters)
            return self._fetch_tasks(session, filters)

    def get_summary(self, client_id: str | None = None) -> WorkCenterSummaryDTO:
        """Get aggregate metrics across all work sections."""
        with self.db_manager.session_scope() as session:
            query = session.query(WorkTaskModel)
            if client_id:
                query = query.filter(WorkTaskModel.client_id == client_id)
            tasks = query.all()

            total = len(tasks)
            todo = sum(1 for t in tasks if t.status == "TODO")
            in_prog = sum(1 for t in tasks if t.status == "IN_PROGRESS")
            wait_cli = sum(1 for t in tasks if t.status == "WAITING_CLIENT")
            wait_rev = sum(1 for t in tasks if t.status == "WAITING_REVIEW")
            completed = sum(1 for t in tasks if t.status == "COMPLETED")
            ai_pending = sum(1 for t in tasks if t.is_confirmed == 0)

            c_flt = WorkCenterFilterDTO(client_id=client_id)
            return WorkCenterSummaryDTO(
                total_tasks=total,
                todo_count=todo,
                in_progress_count=in_prog,
                waiting_client_count=wait_cli,
                waiting_review_count=wait_rev,
                completed_count=completed,
                ai_suggestions_pending_confirmation=ai_pending,
                tasks_count=total,
                compliance_count=len(self._fetch_compliance_items(session, c_flt)),
                reconciliations_count=len(self._fetch_reconciliation_items(session, c_flt)),
                client_requests_count=len(self._fetch_client_requests(session, c_flt)),
                review_notes_count=len(self._fetch_review_notes(session, c_flt)),
                audit_actions_count=len(self._fetch_audit_actions(session, c_flt)),
            )

    def get_open_source_info(self, item_id: str) -> dict[str, Any]:
        """Return diagnostic payload for opening source entity."""
        with self.db_manager.session_scope() as session:
            task = session.query(WorkTaskModel).filter(WorkTaskModel.id == item_id).first()
            if task:
                return {
                    "id": task.id,
                    "type": task.source,
                    "title": task.title,
                    "linked_document": task.linked_document,
                    "linked_workpaper": task.linked_workpaper,
                    "linked_finding": task.linked_finding,
                }
            req = session.query(ClientDocumentRequestModel).filter(ClientDocumentRequestModel.id == item_id).first()
            if req:
                eng = session.get(EngagementModel, req.engagement_id) if req.engagement_id else None
                return {
                    "id": req.id,
                    "type": "CLIENT_REQUEST",
                    "title": req.title,
                    "client_id": eng.client_id if eng else None,
                    "status": req.status,
                }
            wp = session.query(WorkingPaperModel).filter(WorkingPaperModel.id == item_id).first()
            if wp:
                return {"id": wp.id, "type": "WORKPAPER", "title": wp.title, "status": wp.status}
            return {"id": item_id, "type": "GENERIC", "title": "Source Item"}

    def _fetch_tasks(self, session: Session, filters: WorkCenterFilterDTO) -> list[WorkItemDTO]:
        query = session.query(WorkTaskModel)
        if filters.client_id:
            query = query.filter(WorkTaskModel.client_id == filters.client_id)
        if filters.engagement_id:
            query = query.filter(WorkTaskModel.engagement_id == filters.engagement_id)
        if filters.assignee:
            query = query.filter(WorkTaskModel.assignee.ilike(f"%{filters.assignee}%"))
        if filters.status:
            query = query.filter(WorkTaskModel.status == filters.status.upper())
        if filters.priority:
            query = query.filter(WorkTaskModel.priority == filters.priority.upper())
        if filters.search_query:
            query = query.filter(WorkTaskModel.title.ilike(f"%{filters.search_query}%"))
        return [self._task_model_to_dto(session, m) for m in query.order_by(WorkTaskModel.created_at.desc()).all()]

    def _fetch_compliance_items(self, session: Session, filters: WorkCenterFilterDTO) -> list[WorkItemDTO]:
        items = []
        for wp in session.query(WorkingPaperModel).all():
            eng = session.get(EngagementModel, wp.engagement_id) if wp.engagement_id else None
            cid = eng.client_id if eng else None
            if filters.client_id and cid != filters.client_id:
                continue
            if "CARO" in wp.title or "TAX" in wp.title or wp.status in ("PREPARED", "UNDER_REVIEW"):
                c_name = eng.client.name if eng and eng.client else "General Practice"
                items.append(
                    WorkItemDTO(
                        id=f"comp_{wp.id}",
                        section="Compliance",
                        title=f"Statutory Compliance: {wp.title}",
                        description=f"Status: {wp.status} | Area: {wp.area}",
                        client_id=cid,
                        client_name=c_name,
                        engagement_id=wp.engagement_id,
                        assignee=wp.reviewer_id or wp.preparer_id or "Tax Team",
                        created_at=str(wp.created_at),
                        due_at="Statutory Deadline",
                        status="WAITING_REVIEW" if wp.status == "PREPARED" else "TODO",
                        priority="HIGH",
                        source="COMPLIANCE",
                        linked_workpaper=wp.id,
                    )
                )
        return items

    def _fetch_reconciliation_items(self, session: Session, filters: WorkCenterFilterDTO) -> list[WorkItemDTO]:
        items = []
        for wp in session.query(WorkingPaperModel).filter(WorkingPaperModel.area.ilike("%reconcil%")).all():
            eng = session.get(EngagementModel, wp.engagement_id) if wp.engagement_id else None
            cid = eng.client_id if eng else None
            if filters.client_id and cid != filters.client_id:
                continue
            c_name = eng.client.name if eng and eng.client else "General Practice"
            items.append(
                WorkItemDTO(
                    id=f"recon_{wp.id}",
                    section="Reconciliations",
                    title=f"Reconciliation Review: {wp.title}",
                    description=f"Area: {wp.area} | Status: {wp.status}",
                    client_id=cid,
                    client_name=c_name,
                    engagement_id=wp.engagement_id,
                    assignee=wp.preparer_id or "Audit Team",
                    created_at=str(wp.created_at),
                    due_at="N/A",
                    status="IN_PROGRESS" if wp.status == "DRAFT" else "TODO",
                    priority="MEDIUM",
                    source="RECONCILIATION",
                    linked_workpaper=wp.id,
                )
            )
        return items

    def _fetch_client_requests(self, session: Session, filters: WorkCenterFilterDTO) -> list[WorkItemDTO]:
        query = session.query(ClientDocumentRequestModel)
        if filters.client_id:
            query = query.join(EngagementModel, ClientDocumentRequestModel.engagement_id == EngagementModel.id).filter(
                EngagementModel.client_id == filters.client_id
            )
        items = []
        for r in query.all():
            eng = session.get(EngagementModel, r.engagement_id)
            cid = eng.client_id if eng else None
            c_name = eng.client.name if eng and eng.client else "General Practice"
            st = "WAITING_CLIENT" if r.status in ("REQUESTED", "OVERDUE") else "WAITING_REVIEW"
            items.append(
                WorkItemDTO(
                    id=r.id,
                    section="Client Requests",
                    title=f"Client Request: {r.title}",
                    description=r.description or "PBC Document Request",
                    client_id=cid,
                    client_name=c_name,
                    engagement_id=r.engagement_id,
                    assignee="Client Portal",
                    created_at=str(r.created_at),
                    due_at=r.due_date or "N/A",
                    status=st,
                    priority="HIGH" if r.status == "OVERDUE" else "MEDIUM",
                    source="CLIENT_REQUEST",
                    linked_document=r.id,
                )
            )
        return items

    def _fetch_review_notes(self, session: Session, filters: WorkCenterFilterDTO) -> list[WorkItemDTO]:
        items = []
        for wp in session.query(WorkingPaperModel).filter(WorkingPaperModel.status == "PREPARED").all():
            eng = session.get(EngagementModel, wp.engagement_id) if wp.engagement_id else None
            cid = eng.client_id if eng else None
            if filters.client_id and cid != filters.client_id:
                continue
            c_name = eng.client.name if eng and eng.client else "General Practice"
            items.append(
                WorkItemDTO(
                    id=f"rev_{wp.id}",
                    section="Review Notes",
                    title=f"Working Paper Review: {wp.title}",
                    description=f"Awaiting partner/manager review for area {wp.area}",
                    client_id=cid,
                    client_name=c_name,
                    engagement_id=wp.engagement_id,
                    assignee=wp.reviewer_id or "Audit Manager",
                    created_at=str(wp.created_at),
                    due_at="N/A",
                    status="WAITING_REVIEW",
                    priority="HIGH",
                    source="AUDIT",
                    linked_workpaper=wp.id,
                )
            )
        return items

    def _fetch_audit_actions(self, session: Session, filters: WorkCenterFilterDTO) -> list[WorkItemDTO]:
        items = []
        for f in session.query(AuditFindingModel).all():
            eng = session.get(EngagementModel, f.engagement_id) if f.engagement_id else None
            cid = eng.client_id if eng else None
            if filters.client_id and cid != filters.client_id:
                continue
            c_name = eng.client.name if eng and eng.client else "General Practice"
            items.append(
                WorkItemDTO(
                    id=f"action_{f.id}",
                    section="Audit Actions",
                    title=f"Audit Finding: {f.title}",
                    description=f"Severity: {f.severity} | Category: {f.category}",
                    client_id=cid,
                    client_name=c_name,
                    engagement_id=f.engagement_id,
                    assignee="Audit Team",
                    created_at=str(f.created_at),
                    due_at="N/A",
                    status="IN_PROGRESS" if f.status == "OPEN" else "COMPLETED",
                    priority="URGENT" if f.severity == "CRITICAL" else "HIGH",
                    source="AUDIT",
                    linked_finding=f.id,
                )
            )
        return items

    def _task_model_to_dto(self, session: Session, m: WorkTaskModel) -> WorkItemDTO:
        c_name = m.client.name if m.client else "General Practice"
        e_name = m.engagement.audit_type if m.engagement else "N/A"
        fy = f"FY {m.engagement.financial_year}" if m.engagement else "FY 2025-26"
        is_ai = m.source == "AI_SUGGESTION"
        return WorkItemDTO(
            id=m.id,
            section="Tasks",
            title=m.title,
            description=m.description or "",
            client_id=m.client_id,
            client_name=c_name,
            financial_year=fy,
            engagement_id=m.engagement_id,
            engagement_name=e_name,
            assignee=m.assignee or "Unassigned",
            created_at=m.created_at,
            due_at=m.due_at or "N/A",
            status=m.status,
            priority=m.priority,
            source=m.source,
            linked_document=m.linked_document,
            linked_workpaper=m.linked_workpaper,
            linked_finding=m.linked_finding,
            requires_human_confirmation=is_ai and m.is_confirmed == 0,
            is_confirmed=bool(m.is_confirmed),
        )
