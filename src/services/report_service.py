from typing import Dict, Any
from sqlalchemy.orm import Session
from database.models import Engagement, Finding, WorkingPaper
from core.exceptions import EntityNotFoundError

class ReportService:
    """
    Service responsible for generating final Auditor Reports.
    
    Repositories used:
    - Standard SQLAlchemy Session (aggregates across multiple repos implicitly)
    """

    def __init__(self, session: Session):
        self.session = session

    def generate_executive_summary(self, engagement_id: int) -> Dict[str, Any]:
        """Aggregate all findings and materiality to create a report summary."""
        engagement = self.session.query(Engagement).filter(Engagement.id == engagement_id).first()
        if not engagement:
            raise EntityNotFoundError("Engagement not found.")

        # Find all completed WPs
        wps = self.session.query(WorkingPaper).filter(WorkingPaper.index.has(engagement_id=engagement_id)).all()
        wp_ids = [wp.id for wp in wps]

        # Aggregate findings
        findings = self.session.query(Finding).filter(Finding.working_paper_id.in_(wp_ids)).all()
        
        total_impact = sum(f.financial_impact for f in findings if f.financial_impact)
        high_risk_count = sum(1 for f in findings if f.severity == 'High' and not f.is_resolved)

        return {
            "engagement_id": engagement_id,
            "status": engagement.status,
            "total_findings": len(findings),
            "high_risk_unresolved": high_risk_count,
            "total_financial_impact": total_impact
        }
