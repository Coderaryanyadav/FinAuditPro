"""Unit tests for BackupRestoreService archive bundling, encryption, and safe restoration."""

import json
import zipfile

import pytest

from finauditpro.application.services.backup_restore_service import BackupRestoreService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.domain.exceptions import ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_backup_env(tmp_path):
    db_file = tmp_path / "test_backup_m8.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Backup Test Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Backup Test Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    backup_dir = tmp_path / "storage"
    backup_svc = BackupRestoreService(db_manager, storage_dir=str(backup_dir))

    return eng, backup_svc, db_manager, tmp_path


def test_backup_and_restore_round_trip(setup_backup_env) -> None:
    """Verify backup bundling, passphrase encryption, manifest check, and audit chain restore."""
    eng, backup_svc, db_manager, tmp_path = setup_backup_env

    archive_path = str(tmp_path / "backup_archive.zip")
    passphrase = "SecretAuditPassword123!"

    # 1. Create Encrypted Backup
    created_path = backup_svc.create_backup(archive_path, passphrase=passphrase)
    assert created_path == archive_path

    # 2. Restore Backup with Passphrase
    success = backup_svc.restore_backup(archive_path, passphrase=passphrase)
    assert success is True


def test_restore_fails_with_invalid_passphrase(setup_backup_env) -> None:
    """Verify restore fails with ValidationError when invalid passphrase is provided."""
    eng, backup_svc, _, tmp_path = setup_backup_env

    archive_path = str(tmp_path / "encrypted_backup.zip")
    backup_svc.create_backup(archive_path, passphrase="CorrectPassword")

    with pytest.raises(ValidationError) as exc_info:
        backup_svc.restore_backup(archive_path, passphrase="WrongPassword")

    assert "Failed to decrypt" in str(exc_info.value)


def test_encrypted_backups_use_distinct_persisted_salts(setup_backup_env) -> None:
    """Each archive gets an independent salt rather than a reusable encryption key."""
    _, backup_svc, _, tmp_path = setup_backup_env
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    backup_svc.create_backup(str(first), passphrase="CorrectPassword")
    backup_svc.create_backup(str(second), passphrase="CorrectPassword")

    first_bytes = first.read_bytes()
    second_bytes = second.read_bytes()
    magic_len = len(backup_svc._ENCRYPTED_MAGIC)
    salt_end = magic_len + backup_svc._SALT_LENGTH
    assert first_bytes.startswith(backup_svc._ENCRYPTED_MAGIC)
    assert second_bytes.startswith(backup_svc._ENCRYPTED_MAGIC)
    assert first_bytes[magic_len:salt_end] != second_bytes[magic_len:salt_end]


def test_restore_rejects_archive_path_traversal(setup_backup_env) -> None:
    """Untrusted archives cannot write outside the configured backup storage directory."""
    _, backup_svc, _, tmp_path = setup_backup_env
    archive = tmp_path / "unsafe.zip"
    member = "documents/../../outside.txt"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("sha256_manifest.json", json.dumps({member: "not-used"}))
        zf.writestr(member, b"unsafe")

    with pytest.raises(ValidationError, match="unsafe file path"):
        backup_svc.restore_backup(str(archive))
