"""
Role-Based Access Control (RBAC) & Permission Matrix for FinAuditPro.
Defines 6 enterprise roles and permission enforcement rules across screens, actions, and reports.
"""

from enum import Enum
from typing import Set, Dict, List

class UserRole(str, Enum):
    ADMINISTRATOR = "Administrator"
    AUDIT_PARTNER = "Audit Partner"
    SENIOR_AUDITOR = "Senior Auditor"
    JUNIOR_AUDITOR = "Junior Auditor"
    REVIEWER = "Reviewer"
    READ_ONLY = "Read Only"


class Permission(str, Enum):
    VIEW_DASHBOARD = "view_dashboard"
    MANAGE_CLIENTS = "manage_clients"
    UPLOAD_DOCUMENTS = "upload_documents"
    DELETE_DOCUMENTS = "delete_documents"
    RUN_AI_ANALYSIS = "run_ai_analysis"
    MANAGE_RULES = "manage_rules"
    EDIT_WORKING_PAPERS = "edit_working_papers"
    REVIEW_WORKING_PAPERS = "review_working_papers"
    APPROVE_AUDIT = "approve_audit"
    GENERATE_REPORTS = "generate_reports"
    SIGN_REPORTS = "sign_reports"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SETTINGS = "manage_settings"
    PERFORM_BACKUP = "perform_backup"


class RBACManager:
    """Enterprise Permission Matrix and Access Control Enforcer."""

    ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
        UserRole.ADMINISTRATOR: set(Permission),  # Full access to all permissions
        
        UserRole.AUDIT_PARTNER: {
            Permission.VIEW_DASHBOARD,
            Permission.MANAGE_CLIENTS,
            Permission.UPLOAD_DOCUMENTS,
            Permission.DELETE_DOCUMENTS,
            Permission.RUN_AI_ANALYSIS,
            Permission.MANAGE_RULES,
            Permission.EDIT_WORKING_PAPERS,
            Permission.REVIEW_WORKING_PAPERS,
            Permission.APPROVE_AUDIT,
            Permission.GENERATE_REPORTS,
            Permission.SIGN_REPORTS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.MANAGE_SETTINGS,
            Permission.PERFORM_BACKUP,
        },
        
        UserRole.SENIOR_AUDITOR: {
            Permission.VIEW_DASHBOARD,
            Permission.MANAGE_CLIENTS,
            Permission.UPLOAD_DOCUMENTS,
            Permission.RUN_AI_ANALYSIS,
            Permission.MANAGE_RULES,
            Permission.EDIT_WORKING_PAPERS,
            Permission.REVIEW_WORKING_PAPERS,
            Permission.GENERATE_REPORTS,
            Permission.VIEW_AUDIT_LOGS,
        },
        
        UserRole.JUNIOR_AUDITOR: {
            Permission.VIEW_DASHBOARD,
            Permission.UPLOAD_DOCUMENTS,
            Permission.RUN_AI_ANALYSIS,
            Permission.EDIT_WORKING_PAPERS,
            Permission.VIEW_AUDIT_LOGS,
        },
        
        UserRole.REVIEWER: {
            Permission.VIEW_DASHBOARD,
            Permission.RUN_AI_ANALYSIS,
            Permission.REVIEW_WORKING_PAPERS,
            Permission.VIEW_AUDIT_LOGS,
        },
        
        UserRole.READ_ONLY: {
            Permission.VIEW_DASHBOARD,
            Permission.VIEW_AUDIT_LOGS,
        },
    }

    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if role possesses specific permission."""
        role_perms = cls.ROLE_PERMISSIONS.get(role, set())
        return permission in role_perms

    @classmethod
    def get_permissions(cls, role: UserRole) -> List[str]:
        """Get list of permissions for a given role."""
        return [p.value for p in cls.ROLE_PERMISSIONS.get(role, set())]
