from typing import List
from database.repositories.audit_log_repo import AuditLogRepository
from database.models import AuditLog

class AuditTrailService:
    """
    Service responsible for logging immutable audit trails.
    
    Repositories used:
    - AuditLogRepository
    """

    def __init__(self, log_repo: AuditLogRepository):
        self.log_repo = log_repo

    def log_action(self, user_id: int, action: str, target_entity: str, engagement_id: int = None, ip_address: str = None) -> AuditLog:
        """Create an immutable audit log entry."""
        return self.log_repo.log_action(user_id, action, target_entity, engagement_id, ip_address)

    def get_engagement_logs(self, engagement_id: int) -> List[AuditLog]:
        """Fetch all logs for a specific engagement."""
        return self.log_repo.get_by_engagement(engagement_id)
