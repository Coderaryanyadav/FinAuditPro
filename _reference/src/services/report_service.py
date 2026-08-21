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
        from database.models import MaterialityCalculation, Client
        engagement = self.session.query(Engagement).filter(Engagement.id == engagement_id).first()
        if not engagement:
            client = self.session.query(Client).first()
            client_name = client.name if client else "Client"
            status = "Execution"
        else:
            client_name = engagement.client.name if engagement.client else "Client"
            status = engagement.status

        # Aggregate findings linked via WorkingPaper or audit_id
        wps = self.session.query(WorkingPaper).filter(WorkingPaper.index.has(engagement_id=engagement_id)).all()
        wp_ids = [wp.id for wp in wps]

        findings = self.session.query(Finding).filter(
            (Finding.working_paper_id.in_(wp_ids)) | (Finding.audit_id == engagement_id)
        ).all()
        
        total_impact = sum(f.financial_impact for f in findings if f.financial_impact)
        high_risk_count = sum(1 for f in findings if f.severity in ('High', 'CRITICAL') and not f.is_resolved)

        mat = self.session.query(MaterialityCalculation).filter_by(engagement_id=engagement_id).order_by(MaterialityCalculation.id.desc()).first()

        return {
            "engagement_id": engagement_id,
            "client_name": client_name,
            "status": status,
            "total_findings": len(findings),
            "high_risk_unresolved": high_risk_count,
            "total_financial_impact": total_impact,
            "overall_materiality": mat.overall_materiality if mat else None,
            "performance_materiality": mat.performance_materiality if mat else None,
            "findings": findings
        }
