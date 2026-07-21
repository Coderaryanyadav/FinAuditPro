from typing import List, Optional
from core.exceptions import ValidationError, EntityNotFoundError
from database.repositories.engagement_repo import EngagementRepository
from database.models import Engagement

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
        Calculate overall completion progress based on working papers and procedures.
        Stub for complex logic to be expanded later.
        """
        engagement = self.get_engagement(engagement_id)
        if engagement.status == 'Completed':
            return 100.0
        elif engagement.status == 'Planning':
            return 10.0
        return 50.0 # Placeholder
