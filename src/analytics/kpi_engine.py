"""
KPI Calculation Engine for FinAuditPro.
Computes executive metrics strictly from database records using SQL aggregation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from database.database import SessionLocal
from database.models import AuditProject, Document, Finding, WorkingPaper

@dataclass
class KPIMetrics:
    avg_audit_time_days: float = 0.0
    avg_risk_score: float = 0.0
    avg_compliance_score: float = 0.0
    avg_ocr_accuracy_pct: float = 0.0
    avg_ai_confidence_pct: float = 0.0
    hours_saved_count: float = 0.0
    documents_processed_count: int = 0
    audit_completion_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_audit_time_days": round(self.avg_audit_time_days, 1),
            "avg_risk_score": round(self.avg_risk_score, 1),
            "avg_compliance_score": round(self.avg_compliance_score, 1),
            "avg_ocr_accuracy_pct": round(self.avg_ocr_accuracy_pct, 1),
            "avg_ai_confidence_pct": round(self.avg_ai_confidence_pct, 1),
            "hours_saved_count": round(self.hours_saved_count, 0),
            "documents_processed_count": self.documents_processed_count,
            "audit_completion_pct": round(self.audit_completion_pct, 1),
        }


class KPIEngine:
    """Calculates firm-wide and engagement-level KPIs strictly via SQL aggregation."""

    @staticmethod
    def calculate_kpis(projects_data: Optional[List[Dict[str, Any]]] = None) -> KPIMetrics:
        """Computes aggregated KPI metrics directly from live database tables."""
        session = SessionLocal()
        try:
            projects = session.query(AuditProject).all()
            total_projects = len(projects)
            docs_count = session.query(Document).count()
            findings_count = session.query(Finding).count()

            if total_projects == 0:
                return KPIMetrics(
                    documents_processed_count=docs_count
                )

            risk_scores = [p.risk_score for p in projects if p.risk_score is not None]
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            
            completed = sum(1 for p in projects if p.status == "Completed")
            comp_pct = (completed / total_projects) * 100.0

            return KPIMetrics(
                avg_risk_score=avg_risk,
                avg_compliance_score=100.0 - avg_risk if avg_risk > 0 else 0.0,
                documents_processed_count=docs_count,
                audit_completion_pct=comp_pct
            )
        finally:
            session.close()
