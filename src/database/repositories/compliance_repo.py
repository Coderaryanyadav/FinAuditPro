from typing import List, Optional
import datetime
from sqlalchemy.orm import Session
from database.models import ComplianceTask

class ComplianceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_engagement(self, engagement_id: int) -> List[ComplianceTask]:
        return self.session.query(ComplianceTask).filter(ComplianceTask.engagement_id == engagement_id).all()

    def create(self, engagement_id: int, task_name: str, description: str = None, due_date: datetime.datetime = None) -> ComplianceTask:
        task = ComplianceTask(
            engagement_id=engagement_id,
            task_name=task_name,
            description=description,
            due_date=due_date
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def mark_completed(self, task_id: int) -> Optional[ComplianceTask]:
        task = self.session.query(ComplianceTask).filter(ComplianceTask.id == task_id).first()
        if task:
            task.is_completed = True
            self.session.commit()
            self.session.refresh(task)
        return task
