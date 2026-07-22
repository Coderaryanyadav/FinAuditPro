from typing import Dict, Any
from sqlalchemy.orm import Session
from database.models import Client, Engagement, ReviewNote, Finding, ComplianceTask

class DashboardService:
    """
    Service responsible for calculating top-level UI statistics.
    
    Repositories used:
    - SQLAlchemy Session
    """

    def __init__(self, session: Session):
        self.session = session

    def get_global_dashboard_stats(self) -> Dict[str, Any]:
        """Calculate firm-wide statistics."""
        total_clients = self.session.query(Client).count()
        active_engagements = self.session.query(Engagement).filter(Engagement.status != 'Completed').count()
        
        return {
            "total_clients": total_clients,
            "active_engagements": active_engagements
        }

    def get_engagement_dashboard_stats(self, engagement_id: int) -> Dict[str, Any]:
        """Calculate statistics for a specific engagement."""
        from database.models import WorkingPaper, WorkingPaperIndex
        pending_reviews = self.session.query(ReviewNote).join(WorkingPaper).join(WorkingPaperIndex).filter(
            WorkingPaperIndex.engagement_id == engagement_id,
            ReviewNote.status == 'Open'
        ).count()

        open_findings = self.session.query(Finding).filter(
            Finding.audit_id == engagement_id,
            Finding.is_resolved == False
        ).count()

        compliance_tasks = self.session.query(ComplianceTask).filter(ComplianceTask.engagement_id == engagement_id).all()
        completed_tasks = sum(1 for t in compliance_tasks if t.is_completed)
        compliance_percentage = (completed_tasks / len(compliance_tasks) * 100.0) if compliance_tasks else 0.0

        return {
            "pending_reviews": pending_reviews,
            "open_findings": open_findings,
            "compliance_percentage": round(compliance_percentage, 1)
        }
