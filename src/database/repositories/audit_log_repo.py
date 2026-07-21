from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import AuditLog

class AuditLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def log_action(self, user_id: int, action: str, target_entity: str, engagement_id: int = None, ip_address: str = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            target_entity=target_entity,
            engagement_id=engagement_id,
            ip_address=ip_address
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def get_by_engagement(self, engagement_id: int) -> List[AuditLog]:
        return self.session.query(AuditLog).filter(AuditLog.engagement_id == engagement_id).order_by(AuditLog.created_at.desc()).all()

    def get_recent(self, limit: int = 50) -> List[AuditLog]:
        return self.session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
