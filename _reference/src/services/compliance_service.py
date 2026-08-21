from typing import List
import datetime
from database.repositories.compliance_repo import ComplianceRepository
from database.models import ComplianceTask
from core.exceptions import EntityNotFoundError

class ComplianceService:
    """
    Service responsible for managing Compliance Tasks.
    
    Repositories used:
    - ComplianceRepository
    """

    def __init__(self, compliance_repo: ComplianceRepository):
        self.compliance_repo = compliance_repo

    def add_task(self, engagement_id: int, task_name: str, description: str = None, due_date: datetime.datetime = None) -> ComplianceTask:
        """Add a new compliance task."""
        return self.compliance_repo.create(engagement_id, task_name, description, due_date)

    def mark_completed(self, task_id: int) -> ComplianceTask:
        """Mark a task as completed."""
        task = self.compliance_repo.mark_completed(task_id)
        if not task:
            raise EntityNotFoundError(f"Compliance Task {task_id} not found.")
        return task

    def get_tasks(self, engagement_id: int) -> List[ComplianceTask]:
        """Get all tasks for an engagement."""
        return self.compliance_repo.get_by_engagement(engagement_id)
