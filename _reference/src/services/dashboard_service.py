from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from database.models import Client, AuditProject, Engagement, ReviewNote, Finding, ComplianceTask

class DashboardService:
    """
    Service responsible for calculating top-level UI statistics.
    
    Repositories used:
    - SQLAlchemy Session
    """

    def __init__(self, session: Session):
        self.session = session

    def get_global_dashboard_stats(self) -> Dict[str, Any]:
        """Calculate firm-wide statistics."""
        total_clients = self.session.query(Client).count()
        active_engagements = self.session.query(Engagement).filter(Engagement.status != 'Completed').count()
        
        return {
            "total_clients": total_clients,
            "active_engagements": active_engagements
        }

    def get_engagement_dashboard_stats(self, engagement_id: int) -> Dict[str, Any]:
        """Calculate statistics for a specific engagement."""
        from database.models import WorkingPaper, WorkingPaperIndex
        pending_reviews = self.session.query(ReviewNote).join(WorkingPaper).join(WorkingPaperIndex).filter(
            WorkingPaperIndex.engagement_id == engagement_id,
            ReviewNote.status == 'Open'
        ).count()

        open_findings = self.session.query(Finding).filter(
            Finding.audit_id == engagement_id,
            Finding.is_resolved == False
        ).count()

        compliance_tasks = self.session.query(ComplianceTask).filter(ComplianceTask.engagement_id == engagement_id).all()
        completed_tasks = sum(1 for t in compliance_tasks if t.is_completed)
        compliance_percentage = (completed_tasks / len(compliance_tasks) * 100.0) if compliance_tasks else 0.0

        return {
            "pending_reviews": pending_reviews,
            "open_findings": open_findings,
            "compliance_percentage": round(compliance_percentage, 1)
        }

    def load_client_name_cache(self, client_ids: set) -> Dict[int, str]:
        """Fetch client names for a set of client IDs in a single query."""
        if not client_ids:
            return {}
        clients = self.session.query(Client).filter(Client.id.in_(client_ids)).all()
        return {c.id: c.name for c in clients}

    def search_clients_and_findings(self, query: str, limit: int = 3) -> Tuple[List[Client], List[Finding]]:
        """Full-text search across clients and findings."""
        clients = self.session.query(Client).filter(Client.name.ilike(f"%{query}%")).limit(limit).all()
        findings = self.session.query(Finding).filter(Finding.description.ilike(f"%{query}%")).limit(limit).all()
        return clients, findings

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Retrieve dashboard metric card values and recent audit projects."""
        total_clients = self.session.query(Client).count()
        completed_audits = self.session.query(AuditProject).filter_by(status='Completed').count()
        pending_reviews = self.session.query(AuditProject).filter_by(status='Pending Review').count()
        high_risk_cases = self.session.query(AuditProject).filter_by(risk_level='High').count()
        recent_projects = self.session.query(AuditProject).order_by(AuditProject.id.desc()).limit(10).all()
        return {
            "total_clients": total_clients,
            "completed_audits": completed_audits,
            "pending_reviews": pending_reviews,
            "high_risk_cases": high_risk_cases,
            "recent_projects": recent_projects,
        }

    def create_audit_project(self, client_id: int, financial_year: str, status: str, risk_level: str) -> AuditProject:
        """Create and persist a new AuditProject."""
        proj = AuditProject(client_id=client_id, financial_year=financial_year, status=status, risk_level=risk_level)
        self.session.add(proj)
        self.session.commit()
        return proj

    def get_clients_with_projects(self) -> List[Tuple[Client, Optional[AuditProject]]]:
        """Return list of (Client, AuditProject) tuples for the engagement selector."""
        return self.session.query(Client, AuditProject).outerjoin(
            AuditProject, Client.id == AuditProject.client_id
        ).all()

    def get_audit_project(self, project_id: int) -> Optional[AuditProject]:
        """Load a single audit project by ID."""
        return self.session.query(AuditProject).filter_by(id=project_id).first()

    def get_or_create_client_project(self, client_id: int) -> AuditProject:
        """Create an auto-project for a client if none exists."""
        proj = self.session.query(AuditProject).filter_by(client_id=client_id).order_by(AuditProject.id.desc()).first()
        if not proj:
            proj = AuditProject(client_id=client_id, financial_year="2025-26", status="Execution", risk_level="Medium")
            self.session.add(proj)
            self.session.commit()
        return proj

    def get_audit_logs(self) -> List[Any]:
        """Fetch audit log entries after verifying VIEW_AUDIT_LOGS permission."""
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        from core.exceptions import AuthError
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.VIEW_AUDIT_LOGS):
            raise AuthError("User role lacks permission VIEW_AUDIT_LOGS to inspect audit trail logs.")
        from database.models import AuditLog
        return self.session.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()

    def update_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update system settings after verifying MANAGE_SETTINGS permission."""
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        from core.exceptions import AuthError
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_SETTINGS):
            raise AuthError("User role lacks permission MANAGE_SETTINGS to modify application settings.")
        return settings_data
