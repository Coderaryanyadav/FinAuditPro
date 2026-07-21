"""
Unit Tests for FinAuditPro Enterprise Security & Governance.
Tests RBAC, Password Hashing, Session Tokens, AES-256 Crypto, Immutable Audit Logs, and Backup Recovery.
"""

import unittest
import os
import tempfile

from security.rbac import UserRole, Permission, RBACManager
from security.auth import PasswordHasher, AuthManager
from security.crypto import AESCryptoEngine, SecureStorage
from security.audit_trail import ImmutableAuditLogger
from security.backup import BackupEngine
from security.crash_recovery import CrashRecoveryManager, SessionState


class TestSecurityArchitecture(unittest.TestCase):

    def test_rbac_permissions(self):
        # Admin has all permissions
        self.assertTrue(RBACManager.has_permission(UserRole.ADMINISTRATOR, Permission.APPROVE_AUDIT))
        # Read Only does not have approve audit permission
        self.assertFalse(RBACManager.has_permission(UserRole.READ_ONLY, Permission.APPROVE_AUDIT))

    def test_password_hasher(self):
        password = "SecretPassword123!"
        hashed = PasswordHasher.hash_password(password)
        self.assertTrue(PasswordHasher.verify_password(password, hashed))
        self.assertFalse(PasswordHasher.verify_password("WrongPassword", hashed))

    def test_auth_manager_session(self):
        auth = AuthManager(session_timeout_minutes=60)
        session = auth.create_session(user_id=1, user_email="ca@example.com", role=UserRole.AUDIT_PARTNER.value)
        self.assertIsNotNone(session.token_str)
        
        val_session = auth.validate_session(session.token_str)
        self.assertIsNotNone(val_session)
        self.assertEqual(val_session.user_email, "ca@example.com")

    def test_aes_crypto_engine(self):
        engine = AESCryptoEngine(master_password="TestMasterKey")
        original_data = b"Sensitive Audit Data Records"
        encrypted = engine.encrypt_bytes(original_data)
        self.assertNotEqual(encrypted, original_data)
        
        decrypted = engine.decrypt_bytes(encrypted)
        self.assertEqual(decrypted, original_data)

    def test_immutable_audit_logger(self):
        logger = ImmutableAuditLogger()
        entry1 = logger.log_action("user1@example.com", "Partner", "CREATE_CLIENT", "Created TechCorp")
        entry2 = logger.log_action("user1@example.com", "Partner", "UPLOAD_DOC", "Uploaded Invoice")
        
        self.assertEqual(entry2.previous_hash, entry1.entry_hash)
        self.assertTrue(logger.verify_ledger_integrity())

    def test_backup_engine(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_engine = BackupEngine(backup_dir=temp_dir)
            archive = backup_engine.create_backup(db_path="non_existent_db.db", docs_dir="non_existent_dir")
            self.assertTrue(os.path.exists(archive.file_path))
            self.assertTrue(len(archive.sha256_hash) == 64)


if __name__ == "__main__":
    unittest.main()
