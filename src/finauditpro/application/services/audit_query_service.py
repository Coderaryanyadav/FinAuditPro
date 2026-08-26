from uuid import uuid4

from finauditpro.domain.audit_matrix_entities import (
    AuditFinding,
    FindingSourceEnum,
    FindingStatusEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.pbc_and_query_entities import AuditQuery, AuditQueryStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import (
    AuditEventRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_query_repository import (
    AuditQueryRepository,
)


class AuditQueryService:
    """Orchestrates raising audit queries, tracking client responses, and escalating to findings."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def raise_query(
        self,
        engagement_id: str,
        query_text: str,
        audit_area: str,
        working_paper_id: str | None = None,
        procedure_id: str | None = None,
        assigned_to: str = "Associate",
        client_contact: str | None = None,
        evidence_requested: str | None = None,
        due_date: str | None = None,
        actor: str = "Auditor",
    ) -> AuditQuery:
        with self.db_manager.session_scope() as session:
            repo = AuditQueryRepository(session)
            query = AuditQuery(
                id=str(uuid4()),
                engagement_id=engagement_id,
                query_text=query_text,
                audit_area=audit_area,
                working_paper_id=working_paper_id,
                procedure_id=procedure_id,
                assigned_to=assigned_to,
                client_contact=client_contact,
                evidence_requested=evidence_requested,
                due_date=due_date,
                status=AuditQueryStatusEnum.SENT_TO_CLIENT,
            )
            saved = repo.add(query)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor=actor,
                    action="Audit Query Raised",
                    details=f"Raised query in '{audit_area}': '{query_text[:60]}...' (Assigned: {assigned_to}).",
                )
            )
            return saved

    def list_queries(self, engagement_id: str) -> list[AuditQuery]:
        with self.db_manager.session_scope() as session:
            return AuditQueryRepository(session).list_by_engagement(engagement_id)

    def list_queries_for_working_paper(self, working_paper_id: str) -> list[AuditQuery]:
        with self.db_manager.session_scope() as session:
            return AuditQueryRepository(session).list_by_working_paper(working_paper_id)

    def record_client_response(
        self,
        query_id: str,
        response_text: str,
        actor: str = "Client",
    ) -> AuditQuery:
        with self.db_manager.session_scope() as session:
            repo = AuditQueryRepository(session)
            query = repo.get(query_id)
            if not query:
                raise ValueError(f"AuditQuery '{query_id}' not found.")

            query.response_text = response_text
            query.transition_to(AuditQueryStatusEnum.CLIENT_RESPONDED)
            saved = repo.update(query)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=query.engagement_id,
                    actor=actor,
                    action="Query Response Recorded",
                    details=f"Client responded to query '{query_id[:8]}...'. Status set to 'Client Responded'.",
                )
            )
            return saved

    def resolve_query(
        self,
        query_id: str,
        resolution_notes: str,
        reviewer_id: str = "Manager",
        actor: str = "Auditor",
    ) -> AuditQuery:
        with self.db_manager.session_scope() as session:
            repo = AuditQueryRepository(session)
            query = repo.get(query_id)
            if not query:
                raise ValueError(f"AuditQuery '{query_id}' not found.")

            query.resolution_notes = resolution_notes
            query.reviewer_id = reviewer_id
            query.transition_to(AuditQueryStatusEnum.RESOLVED)
            saved = repo.update(query)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=query.engagement_id,
                    actor=actor,
                    action="Audit Query Resolved",
                    details=f"Query '{query_id[:8]}...' resolved by {reviewer_id}. Notes: {resolution_notes}",
                )
            )
            return saved

    def escalate_to_finding(
        self,
        query_id: str,
        finding_title: str,
        finding_description: str,
        severity: RiskSeverityEnum = RiskSeverityEnum.HIGH,
        amount_paise: int | None = None,
        actor: str = "Auditor",
    ) -> tuple[AuditQuery, AuditFinding]:
        """Escalate an unresolved or inadequate client response into a formal AuditFinding."""
        with self.db_manager.session_scope() as session:
            query_repo = AuditQueryRepository(session)
            matrix_repo = AuditMatrixRepository(session)

            query = query_repo.get(query_id)
            if not query:
                raise ValueError(f"AuditQuery '{query_id}' not found.")

            finding = AuditFinding(
                id=str(uuid4()),
                engagement_id=query.engagement_id,
                procedure_id=query.procedure_id,
                title=finding_title,
                description=finding_description,
                category="Unresolved Query Exception",
                severity=severity,
                amount_paise=amount_paise,
                affected_account=query.audit_area,
                status=FindingStatusEnum.OPEN,
                preparer=actor,
                source=FindingSourceEnum.MANUAL,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            saved_finding = matrix_repo.add_finding(finding)

            query.escalated_finding_id = saved_finding.id
            query.transition_to(AuditQueryStatusEnum.ESCALATED_TO_FINDING)
            saved_query = query_repo.update(query)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=query.engagement_id,
                    actor=actor,
                    action="Query Escalated to Audit Finding",
                    details=f"Escalated query '{query_id[:8]}...' to Finding '{saved_finding.title}' (ID: {saved_finding.id[:8]}...).",
                )
            )
            return saved_query, saved_finding
