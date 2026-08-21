"""
Database Encryptor Utility for FinAuditPro.
Provides transparent SQLCipher encryption migration for existing unencrypted SQLite databases.
"""

import os
import shutil
import logging
import tempfile
from typing import Optional, Any

logger = logging.getLogger(__name__)


class EncryptExistingDatabase:
    """Migrates unencrypted SQLite database to AES-256 SQLCipher encrypted database."""

    @classmethod
    def is_database_encrypted(cls, db_path: str) -> bool:
        """Check if DB file is already encrypted (lacks standard SQLite magic header)."""
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            return False
        try:
            with open(db_path, "rb") as f:
                header = f.read(16)
                # Standard SQLite header is b"SQLite format 3\x00"
                return not header.startswith(b"SQLite format 3")
        except Exception:
            return False

    @classmethod
    def run(cls, plain_db_path: str, data_dir: str, passphrase: Optional[str] = None) -> bool:
        """
        Encrypt plain SQLite database using SQLCipher if available.
        Idempotent: skips if already encrypted or plain DB missing.
        """
        if not os.path.exists(plain_db_path):
            return False

        if cls.is_database_encrypted(plain_db_path):
            logger.info("Database is already SQLCipher encrypted or empty.")
            return True

        if not passphrase:
            try:
                from security.crypto import _get_or_create_installation_key
                passphrase = _get_or_create_installation_key(data_dir).hex()
            except Exception as e:
                logger.warning(f"Could not derive encryption key for migration: {e}")
                return False

        sqlcipher_module: Any = None
        try:
            import sqlcipher3 as sqlcipher_module  # type: ignore
        except Exception:
            try:
                from pysqlcipher3 import dbapi2 as sqlcipher_module  # type: ignore
            except Exception:
                sqlcipher_module = None

        temp_enc_path = os.path.join(data_dir, "finauditpro_enc_temp.db")
        backup_path = plain_db_path + ".plain_backup"

        if sqlcipher_module:
            try:
                if os.path.exists(temp_enc_path):
                    os.remove(temp_enc_path)

                conn = sqlcipher_module.connect(plain_db_path)
                cursor = conn.cursor()
                cursor.execute(f"ATTACH DATABASE '{temp_enc_path}' AS encrypted KEY '{passphrase}';")
                cursor.execute("SELECT sqlcipher_export('encrypted');")
                cursor.execute("DETACH DATABASE encrypted;")
                conn.close()

                shutil.copy2(plain_db_path, backup_path)
                shutil.move(temp_enc_path, plain_db_path)
                logger.info("Successfully migrated live SQLite database to AES-256 SQLCipher encrypted storage.")
                return True
            except Exception as e:
                logger.error(f"SQLCipher DB encryption migration failed: {e}")
                if os.path.exists(temp_enc_path):
                    os.remove(temp_enc_path)
                return False
        else:
            logger.warning("SQLCipher module not installed. Live database remains plain SQLite.")
            return False
