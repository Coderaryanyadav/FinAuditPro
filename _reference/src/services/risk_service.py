from typing import List
from database.repositories.risk_repo import RiskRepository
from database.models import Risk, MaterialityCalculation

class RiskService:
    """
    Service responsible for Managing Risks and Materiality calculations.
    
    Repositories used:
    - RiskRepository
    
    Business Rules:
    - Materiality must be calculated based on standard benchmarks (e.g. 5% of Profit Before Tax).
    """

    def __init__(self, risk_repo: RiskRepository):
        self.risk_repo = risk_repo

    def create_risk(self, engagement_id: int, description: str, likelihood: str = 'Medium', impact: str = 'Medium', is_significant: bool = False) -> Risk:
        """Create a new risk assessment."""
        return self.risk_repo.create_risk(engagement_id, description, likelihood, impact, is_significant)

    def calculate_materiality(self, engagement_id: int, benchmark_used: str, benchmark_amount: float) -> MaterialityCalculation:
        """Calculate and store materiality thresholds."""
        # Simple rule: Overall Materiality is 5% of benchmark
        overall = benchmark_amount * 0.05
        # Performance Materiality is 75% of Overall
        performance = overall * 0.75
        # Sum threshold (clearly trivial) is 5% of Overall
        sum_threshold = overall * 0.05
        
        return self.risk_repo.set_materiality(
            engagement_id=engagement_id,
            benchmark_used=benchmark_used,
            benchmark_amount=benchmark_amount,
            overall=overall,
            performance=performance,
            sum_threshold=sum_threshold
        )
