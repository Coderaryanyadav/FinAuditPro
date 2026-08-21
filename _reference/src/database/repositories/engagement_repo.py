from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Engagement, FinancialYear, AuditTeam

class EngagementRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, engagement_id: int) -> Optional[Engagement]:
        return self.session.query(Engagement).filter(Engagement.id == engagement_id).first()

    def get_by_client_id(self, client_id: int) -> List[Engagement]:
        return self.session.query(Engagement).filter(Engagement.client_id == client_id).all()

    def create(self, client_id: int, financial_year_id: int, audit_type: str) -> Engagement:
        engagement = Engagement(
            client_id=client_id,
            financial_year_id=financial_year_id,
            audit_type=audit_type,
            status='Planning'
        )
        self.session.add(engagement)
        self.session.commit()
        self.session.refresh(engagement)
        return engagement

    def update_status(self, engagement_id: int, status: str) -> Optional[Engagement]:
        engagement = self.get_by_id(engagement_id)
        if engagement:
            engagement.status = status
            self.session.commit()
            self.session.refresh(engagement)
        return engagement

    def get_all_financial_years(self) -> List[FinancialYear]:
        return self.session.query(FinancialYear).all()
