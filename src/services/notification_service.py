from typing import List, Dict
import datetime
from sqlalchemy.orm import Session
from database.models import ComplianceTask, ReviewNote

class NotificationService:
    """
    Service responsible for generating system alerts and notifications.
    
    Repositories used:
    - SQLAlchemy Session
    """

    def __init__(self, session: Session):
        self.session = session

    def get_upcoming_deadlines(self, engagement_id: int, days_threshold: int = 7) -> List[Dict[str, str]]:
        """Find compliance tasks due within the threshold days."""
        target_date = datetime.datetime.utcnow() + datetime.timedelta(days=days_threshold)
        
        tasks = self.session.query(ComplianceTask).filter(
            ComplianceTask.engagement_id == engagement_id,
            ComplianceTask.is_completed == False,
            ComplianceTask.due_date <= target_date
        ).all()
        
        return [{"type": "Deadline", "message": f"Task '{t.task_name}' is due on {t.due_date.strftime('%Y-%m-%d')}"} for t in tasks]

    def get_pending_user_reviews(self, user_id: int) -> List[Dict[str, str]]:
        """Find review notes assigned to a specific user that are still open."""
        notes = self.session.query(ReviewNote).filter(
            ReviewNote.assigned_to_id == user_id,
            ReviewNote.status == 'Open'
        ).all()
        
        return [{"type": "Review", "message": f"You have an open review note: {n.note_text[:30]}..."} for n in notes]
