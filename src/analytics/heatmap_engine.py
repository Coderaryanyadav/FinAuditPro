"""
Risk & Compliance Heatmap Engine for FinAuditPro.
Generates 2D heatmap matrices across industries and risk severities strictly from DB queries.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from database.database import SessionLocal
from database.models import Client, Finding, AuditProject

@dataclass
class HeatmapData:
    x_categories: List[str] = field(default_factory=lambda: ["Low", "Medium", "High", "Critical"])
    y_industries: List[str] = field(default_factory=list)
    matrix_scores: List[List[int]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_categories": self.x_categories,
            "y_industries": self.y_industries,
            "matrix_scores": self.matrix_scores,
        }


class HeatmapEngine:
    """Generates matrix data representations for risk heatmaps from live database records."""

    @staticmethod
    def generate_industry_risk_heatmap() -> HeatmapData:
        session = SessionLocal()
        try:
            clients = session.query(Client).all()
            if not clients:
                return HeatmapData()

            industries = list(set([c.industry or "Unspecified" for c in clients]))
            matrix = []
            for ind in industries:
                # Count findings per severity level for clients in this industry
                ind_clients = [c.id for c in clients if (c.industry or "Unspecified") == ind]
                ind_projects = session.query(AuditProject.id).filter(AuditProject.client_id.in_(ind_clients)).all()
                proj_ids = [p[0] for p in ind_projects]
                
                low = session.query(Finding).filter(Finding.audit_id.in_(proj_ids), Finding.risk_level == "Low").count() if proj_ids else 0
                med = session.query(Finding).filter(Finding.audit_id.in_(proj_ids), Finding.risk_level == "Medium").count() if proj_ids else 0
                high = session.query(Finding).filter(Finding.audit_id.in_(proj_ids), Finding.risk_level == "High").count() if proj_ids else 0
                crit = session.query(Finding).filter(Finding.audit_id.in_(proj_ids), Finding.risk_level == "Critical").count() if proj_ids else 0
                
                matrix.append([low, med, high, crit])

            return HeatmapData(
                y_industries=industries,
                matrix_scores=matrix
            )
        finally:
            session.close()
