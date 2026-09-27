"""Engagement application service managing lifecycle, state transitions, and dashboard metrics."""

from sqlalchemy import func, select

from finauditpro.application.dtos import (
    CreateEngagementDTO,
    DashboardSummaryDTO,
    EngagementDashboardDTO,
    UpdateEngagementDTO,
)
from finauditpro.application.engagement_context import current_context
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent, Engagement, EngagementStatusEnum
from finauditpro.domain.engagement_state_machine import EngagementStateMachine
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import (
    AuditFindingModel,
    AuditRiskModel,
    FinancialDatasetModel,
    MaterialityAssessmentModel,
)
from finauditpro.infrastructure.persistence.pbc_and_query_models import ClientDocumentRequestModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)
from finauditpro.infrastructure.persistence.working_paper_models import (
    ReviewNoteModel,
    WorkingPaperModel,
)


class EngagementService:
    """Service handling audit engagement operations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_engagement(self, dto: CreateEngagementDTO) -> Engagement:
        with self.db_manager.session_scope() as session:
            if not FirmRepository(session).get_by_id(dto.firm_id):
                raise EntityNotFoundError("Firm", dto.firm_id)
            if not ClientRepository(session).get_by_id(dto.client_id):
                raise EntityNotFoundError("Client", dto.client_id)

            engagement = Engagement(
                firm_id=dto.firm_id,
                client_id=dto.client_id,
                financial_year=dto.financial_year,
                audit_type=dto.audit_type,
                status=dto.status,
                partner=dto.partner,
                manager=dto.manager,
                assigned_team=dto.assigned_team,
                start_date=dto.start_date,
                reporting_date=dto.reporting_date,
            )
            created = EngagementRepository(session).add(engagement)
            AuditEventRepository(session).add(
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
            engagement = EngagementRepository(session).get_by_id(engagement_id)
            if not engagement:
                raise EntityNotFoundError("Engagement", engagement_id)
            return engagement

    get_engagement_by_id = get_engagement

    def list_engagements_for_client(self, client_id: str) -> list[Engagement]:
        with self.db_manager.session_scope() as session:
            return EngagementRepository(session).list_by_client(client_id)

    def list_engagements_for_firm(self, firm_id: str) -> list[Engagement]:
        with self.db_manager.session_scope() as session:
            return EngagementRepository(session).list_by_firm(firm_id)

    def list_all_engagements(self) -> list[Engagement]:
        with self.db_manager.session_scope() as session:
            return EngagementRepository(session).list_all()

    def update_engagement(self, engagement_id: str, dto: UpdateEngagementDTO) -> Engagement:
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            existing = repo.get_by_id(engagement_id)
            if not existing:
                raise EntityNotFoundError("Engagement", engagement_id)

            if dto.status is not None and dto.status != existing.status:
                EngagementStateMachine.validate_transition(existing.status, dto.status)
                existing.status = dto.status

            for attr in ("financial_year", "audit_type", "partner", "manager", "assigned_team", "start_date", "reporting_date"):
                val = getattr(dto, attr, None)
                if val is not None:
                    setattr(existing, attr, val)

            existing.version = getattr(existing, "version", 1) + 1
            existing.updated_at = utc_now()
            updated = repo.update(existing)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=updated.id,
                    actor="System",
                    action="Engagement Updated",
                    details=f"Updated engagement {updated.id} status to '{updated.status.value}'",
                )
            )
            return updated

    def transition_engagement_status(
        self, engagement_id: str, new_status: EngagementStatusEnum, actor: str = "Lead Auditor"
    ) -> Engagement:
        """Explicitly transition an engagement lifecycle state with full audit logging."""
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            existing = repo.get_by_id(engagement_id)
            if not existing:
                raise EntityNotFoundError("Engagement", engagement_id)

            meta = EngagementStateMachine.validate_transition(existing.status, new_status)
            old_status = existing.status
            existing.status = new_status
            existing.version = getattr(existing, "version", 1) + 1
            existing.updated_at = utc_now()
            updated = repo.update(existing)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=updated.id,
                    actor=actor,
                    action=meta.audit_event_action if meta else "Engagement Lifecycle Transition",
                    details=f"Transitioned status from '{old_status.value}' to '{new_status.value}'. Preconditions: {meta.preconditions if meta else 'N/A'}",
                )
            )

            if current_context.state.engagement_id == engagement_id:
                current_context.update_status(new_status.value)

            return updated

    def lock_engagement(self, engagement_id: str, locked_by: str = "Partner") -> Engagement:
        """Lock and seal an engagement, preventing further modifications."""
        with self.db_manager.session_scope() as session:
            repo = EngagementRepository(session)
            existing = repo.get_by_id(engagement_id)
            if not existing:
                raise EntityNotFoundError("Engagement", engagement_id)
            existing.status = EngagementStatusEnum.COMPLETED
            existing.version = getattr(existing, "version", 1) + 1
            existing.updated_at = utc_now()
            updated = repo.update(existing)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=updated.id,
                    actor=locked_by,
                    action="Engagement Sealed and Locked",
                    details=f"Engagement {updated.id} finalized and cryptographically locked by {locked_by}.",
                )
            )
            return updated

    def get_engagement_dashboard(self, engagement_id: str) -> EngagementDashboardDTO:
        """Aggregate comprehensive engagement-centric metrics for the dashboard."""
        with self.db_manager.session_scope() as session:
            engagement = EngagementRepository(session).get_by_id(engagement_id)
            if not engagement:
                raise EntityNotFoundError("Engagement", engagement_id)

            client = ClientRepository(session).get_by_id(engagement.client_id)
            firm = FirmRepository(session).get_by_id(engagement.firm_id)
            client_name = client.name if client else "Unknown Client"
            firm_name = firm.name if firm else "Unknown Firm"

            # Working papers & Completion percentage
            wp_stmt = select(WorkingPaperModel).where(WorkingPaperModel.engagement_id == engagement_id)
            wps = session.scalars(wp_stmt).all()
            wp_ids = [wp.id for wp in wps]
            total_wps = len(wps)
            completed_wps = sum(
                1 for wp in wps
                if getattr(wp, "status", "").lower() in ("partner_approved", "partner approved", "completed", "approved", "locked")
            )
            open_wps = total_wps - completed_wps
            pct = round((completed_wps / total_wps * 100.0), 1) if total_wps > 0 else 0.0

            # Review notes
            if wp_ids:
                notes = session.scalars(select(ReviewNoteModel).where(ReviewNoteModel.working_paper_id.in_(wp_ids))).all()
            else:
                notes = []
            open_notes = sum(1 for n in notes if getattr(n, "status", "Open") == "Open")
            addressed_notes = sum(1 for n in notes if getattr(n, "status", "") == "Addressed")
            cleared_notes = sum(1 for n in notes if getattr(n, "status", "") == "Cleared")

            # Outstanding PBC & findings
            pbc_stmt = select(ClientDocumentRequestModel).where(
                ClientDocumentRequestModel.engagement_id == engagement_id,
                ClientDocumentRequestModel.status.in_(["Pending", "Requested", "Open"]),
            )
            outstanding_pbc = len(session.scalars(pbc_stmt).all())

            findings_stmt = select(AuditFindingModel).where(
                AuditFindingModel.engagement_id == engagement_id,
                AuditFindingModel.status == "Open",
            )
            unresolved_findings = len(session.scalars(findings_stmt).all())

            # High risk areas
            risks_stmt = select(AuditRiskModel).where(
                AuditRiskModel.engagement_id == engagement_id,
                (AuditRiskModel.derived_romm == "High") | (AuditRiskModel.is_significant_risk == 1),
            )
            high_risks = session.scalars(risks_stmt).all()
            high_risk_areas = [r.title or r.category for r in high_risks]

            # Materiality
            mat_stmt = (
                select(MaterialityAssessmentModel)
                .where(MaterialityAssessmentModel.engagement_id == engagement_id)
                .order_by(MaterialityAssessmentModel.created_at.desc())
            )
            mat = session.scalars(mat_stmt).first()
            mat_overall = mat.overall_materiality_paise if mat else 0
            mat_perf = mat.performance_materiality_paise if mat else 0
            mat_trivial = mat.clearly_trivial_threshold_paise if mat else 0

            # Financial data status
            ds_stmt = (
                select(FinancialDatasetModel)
                .where(FinancialDatasetModel.engagement_id == engagement_id)
                .order_by(FinancialDatasetModel.created_at.desc())
            )
            datasets = session.scalars(ds_stmt).all()
            if datasets:
                latest_ds = datasets[0]
                fin_status = f"Imported ({latest_ds.row_count} rows)"
                tb_balanced = bool(getattr(latest_ds, "is_balanced", True))
            else:
                fin_status = "Pending Import"
                tb_balanced = False

            is_locked = engagement.status in (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.ARCHIVED)
            if is_locked:
                finalisation_status = f"Locked ({engagement.status.value})"
            elif open_notes > 0:
                finalisation_status = f"Blocked ({open_notes} open review notes)"
            elif total_wps > 0 and open_wps == 0:
                finalisation_status = "Ready for Partner Sign-off"
            else:
                finalisation_status = f"{engagement.status.value} Stage"

            return EngagementDashboardDTO(
                engagement_id=engagement.id,
                client_id=engagement.client_id,
                client_name=client_name,
                firm_id=engagement.firm_id,
                firm_name=firm_name,
                financial_year=engagement.financial_year,
                engagement_type=engagement.audit_type.value,
                status=engagement.status.value,
                partner=engagement.partner,
                manager=engagement.manager,
                team=engagement.assigned_team or [],
                start_date=engagement.start_date,
                reporting_date=engagement.reporting_date,
                version=getattr(engagement, "version", 1) or 1,
                completion_percentage=pct,
                open_working_papers=open_wps,
                total_working_papers=total_wps,
                open_review_notes=open_notes,
                addressed_review_notes=addressed_notes,
                cleared_review_notes=cleared_notes,
                outstanding_pbc=outstanding_pbc,
                unresolved_findings=unresolved_findings,
                high_risk_areas=high_risk_areas,
                materiality_overall_paise=mat_overall,
                materiality_performance_paise=mat_perf,
                materiality_trivial_paise=mat_trivial,
                financial_data_status=fin_status,
                tb_balanced=tb_balanced,
                finalisation_status=finalisation_status,
                is_locked=is_locked,
            )

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
                1 for e in engagements
                if e.status not in (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.ARCHIVED)
            )
            completed_eng = sum(1 for e in engagements if e.status == EngagementStatusEnum.COMPLETED)

            # Count actual open findings across relevant engagements
            open_findings_count = 0
            pending_docs_count = 0
            if engagements:
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

                pbc_stmt = (
                    select(func.count())
                    .select_from(ClientDocumentRequestModel)
                    .where(
                        ClientDocumentRequestModel.engagement_id.in_(eng_ids),
                        ClientDocumentRequestModel.status.in_(["Pending", "Requested", "Open"]),
                    )
                )
                pending_docs_count = session.scalar(pbc_stmt) or 0

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
                pending_documents=pending_docs_count,
                open_findings=open_findings_count,
                recent_activities=activities,
            )
