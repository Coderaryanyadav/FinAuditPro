"""Backup and restore service providing portable, integrity-checked, and encrypted archives."""

import base64
import hashlib
import json
import os
import secrets
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import text

from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import AuditIntegrityError, ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository


class BackupRestoreService:
    """Service managing portable engagement backups with SHA-256 manifest verification and Fernet encryption."""

    _ENCRYPTED_MAGIC = b"FAPB1"
    _SALT_LENGTH = 16
    _LEGACY_SALT = b"finauditpro_salt_m8"

    def __init__(self, db_manager: DatabaseManager, storage_dir: str | Path | None = None) -> None:
        self.db_manager = db_manager
        database_path = Path(str(db_manager.engine.url.database))
        self.storage_dir = Path(storage_dir) if storage_dir else database_path.parent / "storage"
        self.doc_dir = self.storage_dir / "documents"
        self.faiss_dir = self.storage_dir / "ai_indices"

        self.doc_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)

    def _derive_fernet_key(self, passphrase: str, salt: bytes) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))
        return Fernet(key)

    @staticmethod
    def _validate_archive_member(name: str) -> PurePosixPath:
        """Reject unsafe or unexpected ZIP members before writing anything to disk."""
        member = PurePosixPath(name)
        if not name or member.is_absolute() or ".." in member.parts:
            raise ValidationError("Backup archive contains an unsafe file path.")
        if member.parts[0] not in {"database", "documents", "ai_indices", "sha256_manifest.json"}:
            raise ValidationError("Backup archive contains an unexpected file path.")
        return member

    def create_backup(self, output_path: str, passphrase: str | None = None) -> str:
        """Create portable backup archive containing DB + Document Store + FAISS indices + SHA-256 Manifest."""
        manifest: dict[str, str] = {}
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_zip_path = output.with_suffix(output.suffix + ".tmp.zip")

        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Archive DB File (Ensure WAL checkpoint occurs first)
            db_path = Path(str(self.db_manager.engine.url.database))
            if db_path.exists() and str(db_path) != ":memory:":
                try:
                    with self.db_manager.engine.connect() as conn:
                        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
                except Exception:
                    pass
                db_bytes = db_path.read_bytes()
                db_hash = hashlib.sha256(db_bytes).hexdigest()
                zf.writestr("database/finauditpro.db", db_bytes)
                manifest["database/finauditpro.db"] = db_hash

            # 2. Archive Document Store
            if self.doc_dir.exists():
                for root, _, files in os.walk(self.doc_dir):
                    for fname in files:
                        fpath = Path(root) / fname
                        rel_name = "documents/" + str(fpath.relative_to(self.doc_dir))
                        fbytes = fpath.read_bytes()
                        manifest[rel_name] = hashlib.sha256(fbytes).hexdigest()
                        zf.writestr(rel_name, fbytes)

            # 3. Archive FAISS Vector Indices
            if self.faiss_dir.exists():
                for root, _, files in os.walk(self.faiss_dir):
                    for fname in files:
                        fpath = Path(root) / fname
                        rel_name = "ai_indices/" + str(fpath.relative_to(self.faiss_dir))
                        fbytes = fpath.read_bytes()
                        manifest[rel_name] = hashlib.sha256(fbytes).hexdigest()
                        zf.writestr(rel_name, fbytes)

            # 4. Write Manifest
            manifest_json = json.dumps(manifest, sort_keys=True)
            zf.writestr("sha256_manifest.json", manifest_json)

        raw_zip_bytes = temp_zip_path.read_bytes()
        temp_zip_path.unlink()

        # Encrypt if passphrase provided
        if passphrase:
            salt = secrets.token_bytes(self._SALT_LENGTH)
            fernet = self._derive_fernet_key(passphrase, salt)
            final_bytes = self._ENCRYPTED_MAGIC + salt + fernet.encrypt(raw_zip_bytes)
        else:
            final_bytes = raw_zip_bytes

        with output.open("wb") as out_f:
            out_f.write(final_bytes)

        # Record Audit Event
        with self.db_manager.session_scope() as session:
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    actor="System Administrator",
                    action="Backup Created",
                    details=f"Created backup archive at '{output_path}' (Encrypted: {bool(passphrase)})",
                )
            )

        return str(output)

    def restore_backup(self, backup_path: str, passphrase: str | None = None) -> bool:
        """Restore DB, documents, and FAISS indices from backup archive, verifying SHA-256 manifest & audit chain."""
        backup = Path(backup_path)
        if not backup.exists():
            raise ValidationError(f"Backup file not found: '{backup_path}'")

        backup_bytes = backup.read_bytes()

        # Decrypt if passphrase provided
        if passphrase:
            try:
                if backup_bytes.startswith(self._ENCRYPTED_MAGIC):
                    salt_start = len(self._ENCRYPTED_MAGIC)
                    salt_end = salt_start + self._SALT_LENGTH
                    if len(backup_bytes) <= salt_end:
                        raise ValidationError("Corrupt encrypted backup archive.")
                    fernet = self._derive_fernet_key(passphrase, backup_bytes[salt_start:salt_end])
                    raw_zip_bytes = fernet.decrypt(backup_bytes[salt_end:])
                else:
                    # Read legacy archives created before per-archive salts were introduced.
                    raw_zip_bytes = self._derive_fernet_key(passphrase, self._LEGACY_SALT).decrypt(
                        backup_bytes
                    )
            except Exception as ex:
                raise ValidationError(
                    "Failed to decrypt backup archive: Invalid passphrase."
                ) from ex
        else:
            if backup_bytes.startswith(self._ENCRYPTED_MAGIC):
                raise ValidationError("This backup is encrypted and requires its passphrase.")
            raw_zip_bytes = backup_bytes

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".zip", prefix="finauditpro-restore-", dir=backup.parent, delete=False
        ) as temp_f:
            temp_f.write(raw_zip_bytes)
            temp_extract_zip = Path(temp_f.name)

        try:
            with zipfile.ZipFile(temp_extract_zip, "r") as zf:
                for info in zf.infolist():
                    self._validate_archive_member(info.filename)
                if "sha256_manifest.json" not in zf.namelist():
                    raise ValidationError("Corrupt backup archive: Missing 'sha256_manifest.json'.")

                manifest = json.loads(zf.read("sha256_manifest.json").decode("utf-8"))
                if not isinstance(manifest, dict):
                    raise ValidationError("Corrupt backup archive: Invalid manifest.")

                # Verify SHA-256 Manifest
                for rel_path, expected_hash in manifest.items():
                    self._validate_archive_member(rel_path)
                    if rel_path not in zf.namelist():
                        raise ValidationError(
                            f"Backup manifest violation: Missing file '{rel_path}'"
                        )
                    file_bytes = zf.read(rel_path)
                    computed_hash = hashlib.sha256(file_bytes).hexdigest()
                    if computed_hash != expected_hash:
                        raise ValidationError(
                            f"Backup integrity failure: Content hash mismatch on '{rel_path}'"
                        )

                # Restore Document Store
                for name in zf.namelist():
                    if name.startswith("documents/") and not name.endswith("/"):
                        rel = name[len("documents/") :]
                        t_path = self.doc_dir / rel
                        t_path.parent.mkdir(parents=True, exist_ok=True)
                        t_path.write_bytes(zf.read(name))

                    elif name.startswith("ai_indices/") and not name.endswith("/"):
                        rel = name[len("ai_indices/") :]
                        t_path = self.faiss_dir / rel
                        t_path.parent.mkdir(parents=True, exist_ok=True)
                        t_path.write_bytes(zf.read(name))

                    elif name == "database/finauditpro.db":
                        db_path_str = str(self.db_manager.engine.url.database)
                        if db_path_str != ":memory:":
                            import sqlite3
                            self.db_manager.engine.dispose()
                            temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
                            try:
                                temp_db.write(zf.read(name))
                                temp_db.close()
                                src_conn = sqlite3.connect(temp_db.name)
                                dst_conn = sqlite3.connect(db_path_str)
                                with dst_conn:
                                    src_conn.backup(dst_conn)
                                src_conn.close()
                                dst_conn.close()
                            finally:
                                Path(temp_db.name).unlink(missing_ok=True)
                            self.db_manager.engine.dispose()
        finally:
            temp_extract_zip.unlink(missing_ok=True)

        # Re-verify Audit Chain Integrity
        with self.db_manager.session_scope() as session:
            audit_repo = AuditEventRepository(session)
            if not audit_repo.verify_chain():
                raise AuditIntegrityError(
                    "Restored database failed SHA-256 audit chain verification!"
                )

            audit_repo.add(
                AuditEvent(
                    actor="System Administrator",
                    action="Backup Restored",
                    details=f"Restored system state from backup archive '{backup_path}'",
                )
            )

        return True
