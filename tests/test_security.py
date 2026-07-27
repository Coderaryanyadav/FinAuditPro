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
        self.assertTrue(hashed.startswith("pbkdf2$600000$"))
        self.assertTrue(PasswordHasher.verify_password(password, hashed))
        self.assertFalse(PasswordHasher.verify_password("WrongPassword", hashed))
        self.assertFalse(PasswordHasher.needs_rehash(hashed))

        # Test legacy unversioned hash format (salt$hash with 100k iterations)
        import hashlib, os
        salt = os.urandom(16)
        legacy_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        legacy_hash = f"{salt.hex()}${legacy_bytes.hex()}"
        self.assertTrue(PasswordHasher.verify_password(password, legacy_hash))
        self.assertTrue(PasswordHasher.needs_rehash(legacy_hash))

    def test_auth_manager_session(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_file = os.path.join(temp_dir, "sessions.dat")
            auth = AuthManager(session_timeout_minutes=60, storage_path=storage_file)
            session = auth.create_session(user_id=1, user_email="ca@example.com", role=UserRole.AUDIT_PARTNER.value)
            self.assertIsNotNone(session.token_str)
            
            val_session = auth.validate_session(session.token_str)
            self.assertIsNotNone(val_session)
            self.assertEqual(val_session.user_email, "ca@example.com")

    def test_auth_manager_session_persistence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_file = os.path.join(temp_dir, "sessions.dat")
            auth1 = AuthManager(session_timeout_minutes=60, storage_path=storage_file)
            s1 = auth1.create_session(user_id=42, user_email="persisted@example.com", role=UserRole.AUDIT_PARTNER.value, is_remember_me=True)
            
            # Restart AuthManager pointing to same storage file
            auth2 = AuthManager(session_timeout_minutes=60, storage_path=storage_file)
            s2 = auth2.validate_session(s1.token_str)
            self.assertIsNotNone(s2)
            self.assertEqual(s2.user_email, "persisted@example.com")
            self.assertTrue(s2.is_remember_me)

            # Test revocation deletes from disk
            auth2.revoke_session(s1.token_str)
            auth3 = AuthManager(session_timeout_minutes=60, storage_path=storage_file)
            self.assertIsNone(auth3.validate_session(s1.token_str))

    def test_session_tampering_protection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_file = os.path.join(temp_dir, "sessions.dat")
            auth1 = AuthManager(session_timeout_minutes=60, storage_path=storage_file)
            s1 = auth1.create_session(user_id=99, user_email="tamper@example.com", role=UserRole.ADMINISTRATOR.value)
            
            # Corrupt storage file with invalid payload
            with open(storage_file, "wb") as f:
                f.write(b"TAMPERED_INVALID_CYPHERTEXT_BYTES")

            # Restart AuthManager — should handle corrupt data gracefully without crash
            auth2 = AuthManager(session_timeout_minutes=60, storage_path=storage_file)
            self.assertIsNone(auth2.validate_session(s1.token_str))

    def test_aes_crypto_engine(self):
        # Master Password Mode
        engine_master = AESCryptoEngine(master_password="TestMasterKey")
        self.assertTrue(engine_master.is_master_password_protected)
        original_data = b"Sensitive Audit Data Records"
        encrypted = engine_master.encrypt_bytes(original_data)
        self.assertNotEqual(encrypted, original_data)
        decrypted = engine_master.decrypt_bytes(encrypted)
        self.assertEqual(decrypted, original_data)

        # Installation Key Mode (Default)
        engine_inst = AESCryptoEngine()
        self.assertFalse(engine_inst.is_master_password_protected)
        enc_inst = engine_inst.encrypt_bytes(original_data)
        dec_inst = engine_inst.decrypt_bytes(enc_inst)
        self.assertEqual(dec_inst, original_data)

        # Cross-key decryption failure test (Master Key != Installation Key)
        with self.assertRaises(Exception):
            engine_inst.decrypt_bytes(encrypted)

    def test_immutable_audit_logger(self):
        logger = ImmutableAuditLogger()
        logger.ledger = []
        logger._last_hash = "0000000000000000000000000000000000000000000000000000000000000000"
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
