from typing import List
from database.repositories.engagement_repo import EngagementRepository
from database.models import FinancialYear
from core.exceptions import EntityNotFoundError

class FinancialYearService:
    """
    Service responsible for managing Financial Years.
    
    Repositories used:
    - EngagementRepository (which has FY methods)
    
    Business Rules:
    - Provides valid financial years for linking to engagements.
    """

    def __init__(self, engagement_repo: EngagementRepository):
        self.engagement_repo = engagement_repo

    def get_all_financial_years(self) -> List[FinancialYear]:
        """Retrieve all defined financial years."""
        return self.engagement_repo.get_all_financial_years()
