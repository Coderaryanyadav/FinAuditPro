from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from api.middleware.rbac import require_permission
from api.schemas.dashboard import DashboardMetrics, SearchResult
from database.models import User
from services.dashboard_service import DashboardService
from security.rbac import Permission

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


@router.get("/audit-logs")
def view_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS))
):
    """View system audit logs (requires VIEW_AUDIT_LOGS permission)."""
    ds = DashboardService(db)
    logs = ds.get_audit_logs()
    return [{"id": getattr(l, 'id', 0), "user_id": getattr(l, 'user_id', 0), "user_email": getattr(l, 'user_email', ''), "action": getattr(l, 'action', ''), "details": getattr(l, 'details', ''), "created_at": str(getattr(l, 'created_at', ''))} for l in logs]


@router.put("/settings")
def update_settings(
    settings_payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_SETTINGS))
):
    """Update system settings (requires MANAGE_SETTINGS permission)."""
    ds = DashboardService(db)
    return ds.update_settings(settings_payload)


@router.post("/backups")
def create_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PERFORM_BACKUP))
):
    """Trigger system backup (requires PERFORM_BACKUP permission)."""
    from security.backup import BackupEngine
    be = BackupEngine()
    archive = be.create_backup()
    return {
        "status": "success",
        "backup_id": archive.backup_id,
        "file_path": archive.file_path,
        "file_size_bytes": archive.file_size_bytes,
        "sha256_hash": archive.sha256_hash,
    }
