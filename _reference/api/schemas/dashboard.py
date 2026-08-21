from pydantic import BaseModel
from typing import List, Dict, Any


class DashboardMetrics(BaseModel):
    total_clients: int
    completed_audits: int
    pending_reviews: int
    high_risk_cases: int


class SearchResult(BaseModel):
    clients: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
