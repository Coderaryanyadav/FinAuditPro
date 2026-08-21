from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from api.middleware.rbac import require_permission
from api.schemas.audit_project import AuditProjectCreate, AuditProjectRead
from database.models import User, AuditProject
from services.dashboard_service import DashboardService
from security.rbac import Permission

router = APIRouter(prefix="/audit-projects", tags=["Audit Projects"])


@router.get("", response_model=List[AuditProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all audit projects."""
    projects = db.query(AuditProject).order_by(AuditProject.id.desc()).all()
    return projects


@router.post("", response_model=AuditProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    request: AuditProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_CLIENTS))
):
    """Create a new audit project."""
    ds = DashboardService(db)
    return ds.create_audit_project(
        client_id=request.client_id,
        financial_year=request.financial_year,
        status=request.status,
        risk_level=request.risk_level
    )


@router.get("/{project_id}", response_model=AuditProjectRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve audit project by ID."""
    ds = DashboardService(db)
    proj = ds.get_audit_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audit project {project_id} not found")
    return proj


@router.post("/{project_id}/approve", response_model=AuditProjectRead)
def approve_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.APPROVE_AUDIT))
):
    """Approve an audit project (requires APPROVE_AUDIT permission)."""
    ds = DashboardService(db)
    proj = ds.get_audit_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audit project {project_id} not found")
    proj.status = "Completed"
    db.commit()
    db.refresh(proj)
    return proj
