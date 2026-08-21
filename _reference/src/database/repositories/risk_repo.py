from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Risk, MaterialityCalculation

class RiskRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_risks_by_engagement(self, engagement_id: int) -> List[Risk]:
        return self.session.query(Risk).filter(Risk.engagement_id == engagement_id).all()

    def create_risk(self, engagement_id: int, description: str, likelihood: str = 'Medium', impact: str = 'Medium', is_significant: bool = False) -> Risk:
        risk = Risk(
            engagement_id=engagement_id,
            description=description,
            likelihood=likelihood,
            impact=impact,
            is_significant=is_significant
        )
        self.session.add(risk)
        self.session.commit()
        self.session.refresh(risk)
        return risk

    def get_materiality(self, engagement_id: int) -> Optional[MaterialityCalculation]:
        return self.session.query(MaterialityCalculation).filter(MaterialityCalculation.engagement_id == engagement_id).first()

    def set_materiality(self, engagement_id: int, benchmark_used: str, benchmark_amount: float, overall: float, performance: float, sum_threshold: float) -> MaterialityCalculation:
        mat = self.get_materiality(engagement_id)
        if not mat:
            mat = MaterialityCalculation(engagement_id=engagement_id)
            self.session.add(mat)
        
        mat.benchmark_used = benchmark_used
        mat.benchmark_amount = benchmark_amount
        mat.overall_materiality = overall
        mat.performance_materiality = performance
        mat.sum_threshold = sum_threshold
        
        self.session.commit()
        self.session.refresh(mat)
        return mat
