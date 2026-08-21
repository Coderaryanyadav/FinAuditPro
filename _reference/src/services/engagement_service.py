from typing import List, Optional
from core.exceptions import ValidationError, EntityNotFoundError
from database.repositories.engagement_repo import EngagementRepository
from database.models import Engagement
from sqlalchemy.exc import SQLAlchemyError

class EngagementService:
    """
    Service responsible for managing Audit Engagements.
    
    Repositories used:
    - EngagementRepository
    
    Business Rules:
    - Status transitions must follow a strict path (Planning -> Execution -> Reporting -> Completed).
    """

    VALID_STATUSES = ['Planning', 'Execution', 'Reporting', 'Completed']

    def __init__(self, engagement_repo: EngagementRepository):
        self.engagement_repo = engagement_repo

    def create_engagement(self, client_id: int, financial_year_id: int, audit_type: str) -> Engagement:
        """Create a new engagement and set initial status to Planning."""
        if not client_id or not financial_year_id or not audit_type:
            raise ValidationError("Client, Financial Year, and Audit Type are required.")
            
        return self.engagement_repo.create(client_id, financial_year_id, audit_type)

    def get_engagement(self, engagement_id: int) -> Engagement:
        """Fetch engagement by ID."""
        engagement = self.engagement_repo.get_by_id(engagement_id)
        if not engagement:
            raise EntityNotFoundError(f"Engagement {engagement_id} not found.")
        return engagement

    def close_engagement(self, engagement_id: int) -> Engagement:
        """Mark engagement as Completed."""
        return self.update_status(engagement_id, 'Completed')

    def update_status(self, engagement_id: int, status: str) -> Engagement:
        """Update engagement status safely."""
        if status not in self.VALID_STATUSES:
            raise ValidationError(f"Invalid status. Must be one of {self.VALID_STATUSES}")
            
        engagement = self.engagement_repo.update_status(engagement_id, status)
        if not engagement:
            raise EntityNotFoundError(f"Engagement {engagement_id} not found.")
        return engagement

    def get_client_engagements(self, client_id: int) -> List[Engagement]:
        """Fetch all engagements for a specific client."""
        return self.engagement_repo.get_by_client_id(client_id)

    def calculate_progress(self, engagement_id: int) -> float:
        """
        Calculate overall completion progress based on workflow manager state and working paper procedures.
        """
        try:
            from workflow.workflow_manager import WorkflowManager
            wm = WorkflowManager()
            if wm.current_state and wm.current_state.engagement_id == engagement_id:
                return round(wm.current_state.completion_percentage, 1)

            from database.models import WorkingPaper, WorkingPaperIndex
            session = self.engagement_repo.session
            wps = session.query(WorkingPaper).join(WorkingPaperIndex).filter(
                WorkingPaperIndex.engagement_id == engagement_id
            ).all()

            if wps:
                completed = sum(1 for wp in wps if getattr(wp, 'status', None) == 'Reviewed' or getattr(wp, 'conclusion', None))
                return round((completed / len(wps)) * 100.0, 1)

            engagement = self.get_engagement(engagement_id)
            if engagement.status == 'Completed':
                return 100.0
            elif engagement.status == 'Planning':
                return 15.0
            elif engagement.status == 'Execution':
                return 60.0
            elif engagement.status == 'Reporting':
                return 85.0
            return 0.0
        except (SQLAlchemyError, ValueError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Error calculating progress for engagement {engagement_id}: {e}")
            return 0.0

    def ensure_engagement_for_project(self, project_id: int) -> Engagement:
        """
        Unifies AuditProject and Engagement data models.
        Ensures a canonical Engagement row exists for the given AuditProject ID.
        """
        session = self.engagement_repo.session
        from database.models import AuditProject, FinancialYear
        proj = session.query(AuditProject).filter_by(id=project_id).first()
        if not proj:
            raise EntityNotFoundError(f"AuditProject {project_id} not found.")

        fy_label = proj.financial_year or "2025-26"
        fy = session.query(FinancialYear).filter_by(label=fy_label).first()
        if not fy:
            import datetime
            start_yr = int(fy_label.split('-')[0]) if '-' in fy_label else 2025
            fy = FinancialYear(
                label=fy_label,
                start_date=datetime.datetime(start_yr, 4, 1),
                end_date=datetime.datetime(start_yr + 1, 3, 31)
            )
            session.add(fy)
            session.flush()

        eng = session.query(Engagement).filter_by(client_id=proj.client_id, financial_year_id=fy.id).first()
        if not eng:
            eng = Engagement(
                client_id=proj.client_id,
                financial_year_id=fy.id,
                audit_type="Statutory Audit",
                status=proj.status or "Execution"
            )
            session.add(eng)
            session.commit()
            session.refresh(eng)
        return eng

