"""
Automated Backup Engine & Disaster Recovery Wizard for FinAuditPro.
Creates compressed encrypted backup archives (.zip) of database and documents, and provides restore validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
import os
import zipfile
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional

import shutil
import tempfile
from security.crypto import AESCryptoEngine, SecureStorage
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@dataclass
class BackupArchive:
    backup_id: str
    file_path: str
    file_size_bytes: int
    sha256_hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"


class BackupEngine:
    """Manages automatic compressed database & document backups with AES-256 encryption."""

    def __init__(self, backup_dir: str = "data/backups", master_password: Optional[str] = None):
        self.backup_dir = backup_dir
        self.crypto = AESCryptoEngine(master_password=master_password)
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, db_path: str = "src/data/finauditpro.db", docs_dir: str = "data/documents") -> BackupArchive:
        """Create an AES-256 encrypted .enc archive containing the database and audit documents."""
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = f"BACKUP_{timestamp_str}"
        archive_name = f"{backup_id}.enc"
        archive_path = os.path.join(self.backup_dir, archive_name)

        storage = SecureStorage()
        temp_zip = storage.create_secure_temp_file(suffix=".zip")

        try:
            with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                # 1. Add database file if exists
                if os.path.exists(db_path):
                    zipf.write(db_path, arcname="database/finauditpro.db")

                # 2. Add document directory if exists
                if os.path.exists(docs_dir):
                    for root, _, files in os.walk(docs_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, docs_dir)
                            zipf.write(full_path, arcname=os.path.join("documents", rel_path))

                # 3. Add manifest
                manifest = {
                    "backup_id": backup_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "db_included": os.path.exists(db_path),
                    "docs_included": os.path.exists(docs_dir),
                }
                zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

            # Compute SHA-256 hash of plaintext zip before encryption
            hasher = hashlib.sha256()
            with open(temp_zip, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            archive_hash = hasher.hexdigest()

            # Encrypt zip archive to archive_path
            self.crypto.encrypt_file(temp_zip, archive_path)
            file_size = os.path.getsize(archive_path)
            logger.info(f"Created encrypted backup archive: {archive_name} ({file_size / (1024*1024):.2f} MB)")

            return BackupArchive(
                backup_id=backup_id,
                file_path=archive_path,
                file_size_bytes=file_size,
                sha256_hash=archive_hash
            )
        finally:
            storage.cleanup()

    def restore_backup(self, backup_path: str, target_db_path: str = "src/data/finauditpro.db", target_docs_dir: str = "data/documents", expected_hash: Optional[str] = None) -> bool:
        """Validate, decrypt, and extract database & document backup archive."""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup archive not found: {backup_path}")

        temp_dir = os.path.join("src", "data", "restore_temp")
        storage = SecureStorage()
        temp_zip = storage.create_secure_temp_file(suffix=".zip")

        try:
            # Decrypt or use zip file directly
            if backup_path.endswith(".enc"):
                self.crypto.decrypt_file(backup_path, temp_zip)
                active_zip = temp_zip
            else:
                active_zip = backup_path

            # Validate SHA-256 hash if provided
            if expected_hash:
                hasher = hashlib.sha256()
                with open(active_zip, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                computed_hash = hasher.hexdigest()
                if computed_hash != expected_hash:
                    raise ValueError(f"Backup integrity check failed: hash mismatch ({computed_hash} != {expected_hash})")

            with zipfile.ZipFile(active_zip, "r") as zipf:
                namelist = zipf.namelist()
                if "manifest.json" not in namelist:
                    raise ValueError("Invalid backup archive: missing manifest.json")

                # Restore Database
                if "database/finauditpro.db" in namelist:
                    zipf.extract("database/finauditpro.db", path=temp_dir)
                    extracted_db = os.path.join(temp_dir, "database", "finauditpro.db")
                    os.makedirs(os.path.dirname(target_db_path), exist_ok=True)
                    shutil.copy(extracted_db, target_db_path)
                    logger.info(f"Restored database from {backup_path} to {target_db_path}")

                # Restore Documents
                doc_entries = [name for name in namelist if name.startswith("documents/") and not name.endswith("/")]
                if doc_entries:
                    os.makedirs(target_docs_dir, exist_ok=True)
                    for entry in doc_entries:
                        zipf.extract(entry, path=temp_dir)
                        rel_doc_path = os.path.relpath(os.path.join(temp_dir, entry), os.path.join(temp_dir, "documents"))
                        dest_doc_path = os.path.join(target_docs_dir, rel_doc_path)
                        os.makedirs(os.path.dirname(dest_doc_path), exist_ok=True)
                        shutil.copy(os.path.join(temp_dir, entry), dest_doc_path)
                    logger.info(f"Restored {len(doc_entries)} document(s) to {target_docs_dir}")

                return True
        except (OSError, IOError, SQLAlchemyError) as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
        finally:
            storage.cleanup()
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
