"""Tests for Final Archive Package, Manifest Generation, SHA-256 Verification, and Retention Policy."""

from pathlib import Path
from uuid import uuid4
import pytest

from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture
def archival_env(tmp_path):
    db_file = tmp_path / "test_archival.db"
    storage_dir = tmp_path / "storage"
    db_manager = initialize_database(db_file)
    eng_id = f"eng-arch-{uuid4().hex[:8]}"

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="partner_arch",
                password_hash="hash",
                salt="salt",
                display_name="CA Ananya Kapoor (Partner)",
                role=RoleEnum.PARTNER,
            )
        )

        firm = Firm(id="firm-arch", name="Archival Audit LLP")
        FirmRepository(session).add(firm)

        client = Client(
            id="client-arch",
            firm_id=firm.id,
            name="Archival Client Pvt Ltd",
            pan_number="AABCA9876F",
            cin_number="U29100MH2022PTC123456",
        )
        ClientRepository(session).add(client)

        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit FY 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.COMPLETED,
        )
        EngagementRepository(session).add(eng)

    return db_manager, eng_id, partner, storage_dir


def test_archive_package_creation_and_manifest(archival_env) -> None:
    db_manager, eng_id, partner, storage_dir = archival_env
    svc = ArchivalService(db_manager, storage_dir=storage_dir)

    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )

    # Freeze and seal finalized engagement
    dto = FreezeAndSealDTO(
        engagement_id=eng_id,
        sealed_by=partner.username,
        report_date="2026-08-30",
        passphrase=None,
        output_dir=str(storage_dir / "sealed_archives"),
        override_justification="Partner authorized freeze and seal.",
    )
    archive = svc.freeze_and_seal_engagement(dto)

    assert archive.engagement_id == eng_id
    assert archive.sealed_by == partner.username
    assert Path(archive.archive_path).exists()
    assert len(archive.sealed_content_hash) == 64
    assert archive.report_date == "2026-08-30"

    # Verify status transitioned to ARCHIVED
    assert svc.get_engagement_status(eng_id) == EngagementStatusEnum.ARCHIVED.value


def test_archive_integrity_and_tamper_detection(archival_env) -> None:
    db_manager, eng_id, partner, storage_dir = archival_env
    svc = ArchivalService(db_manager, storage_dir=storage_dir)

    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )

    dto = FreezeAndSealDTO(
        engagement_id=eng_id,
        sealed_by=partner.username,
        report_date="2026-08-30",
        passphrase=None,
        output_dir=str(storage_dir / "sealed_archives"),
        override_justification="Partner authorized freeze and seal.",
    )
    archive = svc.freeze_and_seal_engagement(dto)

    # 1. Independent verification passes on unmodified archive
    assert svc.verify_archive_package(archive.archive_path) is True

    # 2. Tampering test: modify 1 byte in the archive zip file
    with open(archive.archive_path, "r+b") as f:
        f.seek(100)
        original_byte = f.read(1)
        # Flip the byte
        tampered_byte = bytes([original_byte[0] ^ 0xFF])
        f.seek(100)
        f.write(tampered_byte)

    # 3. Independent verification must detect the tampering and fail
    assert svc.verify_archive_package(archive.archive_path) is False


def test_retention_policy_and_sqc1_timelines(archival_env) -> None:
    db_manager, eng_id, partner, storage_dir = archival_env
    svc = ArchivalService(db_manager, storage_dir=storage_dir)

    cfg = svc.get_or_create_retention_config()
    # Baseline retention policy: 7 years, 60-day assembly deadline, marked as requiring statutory verification
    assert cfg.assembly_period_days == 60
    assert cfg.retention_period_years == 7
    assert cfg.verified_statutory is False

    # Seal and check assembly deadline and retention calculation
    dto = FreezeAndSealDTO(
        engagement_id=eng_id,
        sealed_by=partner.username,
        report_date="2026-08-30",
        passphrase=None,
        output_dir=str(storage_dir / "sealed_archives"),
        override_justification="Partner authorized freeze and seal.",
    )
    archive = svc.freeze_and_seal_engagement(dto)

    # Assembly deadline = report_date + 60 days
    assert archive.assembly_deadline == "2026-10-29"
    # Retention period = report_date + 7 years
    assert archive.retain_until.startswith("2033-")
