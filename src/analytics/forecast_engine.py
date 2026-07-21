"""
Predictive Analytics & Forecasting Engine for FinAuditPro.
Predicts audit completion timelines and resource load strictly using live database records.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from database.database import SessionLocal
from database.models import AuditProject, Finding

@dataclass
class ForecastMetrics:
    predicted_completion_days: float = 0.0
    resource_utilization_pct: float = 0.0
    expected_q4_audits_count: int = 0
    upcoming_risk_vectors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_completion_days": round(self.predicted_completion_days, 1),
            "resource_utilization_pct": round(self.resource_utilization_pct, 1),
            "expected_q4_audits_count": self.expected_q4_audits_count,
            "upcoming_risk_vectors": self.upcoming_risk_vectors,
        }


class ForecastEngine:
    """Computes predictive models for audit resource planning from live database records."""

    @staticmethod
    def forecast_workload(current_engagements_count: int = 0) -> ForecastMetrics:
        """Forecasts completion timelines and resource load based on active database projects."""
        session = SessionLocal()
        try:
            active_count = session.query(AuditProject).filter(AuditProject.status != "Completed").count()
            findings = session.query(Finding).order_by(Finding.id.desc()).limit(3).all()
            
            if active_count == 0:
                return ForecastMetrics()

            est_days = max(1.0, active_count * 1.5)
            utilization = min(100.0, active_count * 10.0)
            vectors = [f.description[:60] for f in findings] if findings else ["No Active Risk Vectors"]

            return ForecastMetrics(
                predicted_completion_days=est_days,
                resource_utilization_pct=utilization,
                expected_q4_audits_count=active_count,
                upcoming_risk_vectors=vectors
            )
        finally:
            session.close()
