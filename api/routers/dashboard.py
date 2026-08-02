from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from api.schemas.dashboard import DashboardMetrics, SearchResult
from database.models import User
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve realtime dashboard metrics."""
    ds = DashboardService(db)
    raw_metrics = ds.get_realtime_metrics()
    return DashboardMetrics(
        total_clients=raw_metrics.get("total_clients", 0),
        completed_audits=raw_metrics.get("completed_audits", 0),
        pending_reviews=raw_metrics.get("pending_reviews", 0),
        high_risk_cases=raw_metrics.get("high_risk_cases", 0)
    )


@router.get("/search", response_model=SearchResult)
def search_dashboard(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full-text search across clients and findings."""
    ds = DashboardService(db)
    clients, findings = ds.search_clients_and_findings(query=q)

    clients_data = [{"id": c.id, "name": c.name, "gst_number": c.gst_number, "pan_number": c.pan_number} for c in clients]
    findings_data = [{"id": f.id, "description": f.description, "severity": getattr(f, "severity", "LOW")} for f in findings]

    return SearchResult(clients=clients_data, findings=findings_data)
