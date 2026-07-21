"""
Master Security Manager Facade for FinAuditPro.
Integrates RBAC, Auth Tokens, AES-256 Encryption, Immutable Audit Logger, Backup Engine, and Crash Recovery.
"""

from typing import Dict, Any, Optional, List
import logging

from .rbac import UserRole, Permission, RBACManager
from .auth import AuthManager, SessionToken, PasswordHasher
from .crypto import AESCryptoEngine, SecureStorage
from .audit_trail import ImmutableAuditLogger, SecurityAuditEntry
from .backup import BackupEngine, BackupArchive
from .crash_recovery import CrashRecoveryManager, SessionState

logger = logging.getLogger(__name__)

class SecurityManager:
    """Master Facade for Enterprise Security & Governance."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityManager, cls).__new__(cls)
            cls._instance.auth_manager = AuthManager()
            cls._instance.crypto_engine = AESCryptoEngine()
            cls._instance.secure_storage = SecureStorage()
            cls._instance.audit_logger = ImmutableAuditLogger()
            cls._instance.backup_engine = BackupEngine()
            cls._instance.recovery_manager = CrashRecoveryManager()
            cls._instance.current_session: Optional[SessionToken] = None
        return cls._instance

    def authenticate_and_login(self, email: str, raw_password: str, stored_password_hash: str, role_str: str, user_id: int = 1) -> Optional[SessionToken]:
        """Authenticate user password and create active session token."""
        if not PasswordHasher.verify_password(raw_password, stored_password_hash):
            self.audit_logger.log_action(email, role_str, "LOGIN_FAILED", "Invalid password credentials")
            return None

        role = UserRole(role_str)
        session = self.auth_manager.create_session(user_id=user_id, user_email=email, role=role.value)
        self.current_session = session

        self.audit_logger.log_action(email, role.value, "LOGIN_SUCCESS", f"Session token created: {session.token_str[:8]}...")
        return session

    def check_permission(self, permission: Permission) -> bool:
        """Check if current active user role possesses permission."""
        if not self.current_session:
            return False

        try:
            role = UserRole(self.current_session.role)
            has_perm = RBACManager.has_permission(role, permission)
            if not has_perm:
                self.audit_logger.log_action(
                    self.current_session.user_email,
                    self.current_session.role,
                    "PERMISSION_DENIED",
                    f"Attempted unauthorized action: {permission.value}"
                )
            return has_perm
        except ValueError:
            return False

    def log_audit_action(self, action: str, details: str = "") -> SecurityAuditEntry:
        """Convenience log action using current session context."""
        email = self.current_session.user_email if self.current_session else "System"
        role = self.current_session.role if self.current_session else "System"
        return self.audit_logger.log_action(email, role, action, details)
