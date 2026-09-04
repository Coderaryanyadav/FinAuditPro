"""Engagement application service."""

from finauditpro.application.dtos import (
    CreateEngagementDTO,
    DashboardSummaryDTO,
    UpdateEngagementDTO,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent, Engagement, EngagementStatusEnum
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)


class EngagementService:
    """Service handling audit engagement operations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_engagement(self, dto: CreateEngagementDTO) -> Engagement:
        with self.db_manager.session_scope() as session:
            firm_repo = FirmRepository(session)
            if not firm_repo.get_by_id(dto.firm_id):
                raise EntityNotFoundError("Firm", dto.firm_id)

            client_repo = ClientRepository(session)
            if not client_repo.get_by_id(dto.client_id):
                raise EntityNotFoundError("Client", dto.client_id)

            engagement = Engagement(
                firm_id=dto.firm_id,
                client_id=dto.client_id,
                financial_year=dto.financial_year,
                audit_type=dto.audit_type,
                status=dto.status,
                assigned_team=dto.assigned_team,
            )

            engagement_repo = EngagementRepository(session)
            created = engagement_repo.add(engagement)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=created.id,
                    actor="System",
                    action="Engagement Created",
                    details=f"Created {created.audit_type.value} engagement for FY {created.financial_year}",
                )
            )

            return created

    def get_engagement(self, engagement_id: str) -> Engagement:
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            engagement = repo.get_by_id(engagement_id)
            if not engagement:
                raise EntityNotFoundError("Engagement", engagement_id)
            return engagement

    get_engagement_by_id = get_engagement

    def list_engagements_for_client(self, client_id: str) -> list[Engagement]:
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            return repo.list_by_client(client_id)

    def list_engagements_for_firm(self, firm_id: str) -> list[Engagement]:
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            return repo.list_by_firm(firm_id)

    def list_all_engagements(self) -> list[Engagement]:
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            return repo.list_all()

    def update_engagement(self, engagement_id: str, dto: UpdateEngagementDTO) -> Engagement:
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            existing = repo.get_by_id(engagement_id)
            if not existing:
                raise EntityNotFoundError("Engagement", engagement_id)

            if dto.financial_year is not None:
                existing.financial_year = dto.financial_year
            if dto.audit_type is not None:
                existing.audit_type = dto.audit_type
            if dto.status is not None:
                existing.status = dto.status
            if dto.assigned_team is not None:
                existing.assigned_team = dto.assigned_team
            existing.updated_at = utc_now()

            updated = repo.update(existing)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=updated.id,
                    actor="System",
                    action="Engagement Updated",
                    details=f"Updated engagement {updated.id} status to '{updated.status.value}'",
                )
            )

            return updated

    def get_dashboard_summary(self, firm_id: str | None = None) -> DashboardSummaryDTO:
        with self.db_manager.session_scope() as session:
            firm_repo = FirmRepository(session)
            client_repo = ClientRepository(session)
            engagement_repo = EngagementRepository(session)
            audit_repo = AuditEventRepository(session)

            firm_name = None
            if firm_id:
                firm = firm_repo.get_by_id(firm_id)
                firm_name = firm.name if firm else None
                clients = client_repo.list_by_firm(firm_id)
                engagements = engagement_repo.list_by_firm(firm_id)
            else:
                clients = client_repo.list_all()
                engagements = engagement_repo.list_all()

            active_eng = sum(
                1
                for e in engagements
                if e.status not in (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.ARCHIVED)
            )
            completed_eng = sum(
                1 for e in engagements if e.status == EngagementStatusEnum.COMPLETED
            )

            # Count actual open findings across relevant engagements
            open_findings_count = 0
            if engagements:
                from sqlalchemy import func, select

                from finauditpro.infrastructure.persistence.models import AuditFindingModel

                eng_ids = [e.id for e in engagements]
                stmt = (
                    select(func.count())
                    .select_from(AuditFindingModel)
                    .where(
                        AuditFindingModel.engagement_id.in_(eng_ids),
                        AuditFindingModel.status.in_(["Open", "Under Review"]),
                    )
                )
                open_findings_count = session.scalar(stmt) or 0

            recent_events = audit_repo.list_recent(limit=10)
            activities = [
                {
                    "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "action": event.action,
                    "details": event.details or "",
                }
                for event in recent_events
            ]

            return DashboardSummaryDTO(
                firm_id=firm_id,
                firm_name=firm_name,
                total_clients=len(clients),
                active_engagements=active_eng,
                completed_engagements=completed_eng,
                pending_documents=0,
                open_findings=open_findings_count,
                recent_activities=activities,
            )
