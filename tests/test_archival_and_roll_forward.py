"""Comprehensive tests for professional engagement archival, package integrity, restore, immutability, partner reopen, and multi-category roll-forward."""

import hashlib
from pathlib import Path
import pytest

from finauditpro.application.archival_dtos import FreezeAndSealDTO, ReopenEngagementDTO
from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.report_dtos import ApproveReportDTO, GenerateReportDTO
from finauditpro.application.roll_forward_dtos import ConfirmTieOutDTO, ExecuteRollForwardDTO
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.backup_restore_service import BackupRestoreService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.roll_forward_service import RollForwardService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.entities import EngagementStatusEnum, RoleEnum
from finauditpro.domain.exceptions import EngagementLockedError, PermissionDeniedError
from finauditpro.domain.roll_forward_entities import CarriedItemDecisionEnum
from finauditpro.domain.working_paper_entities import SignOffLevelEnum, WorkingPaperStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    DocumentRepository,
    EngagementRepository,
    ReportRepository,
    RollForwardRepository,
    WorkingPaperRepository,
)
from finauditpro.infrastructure.persistence.repositories.archival_repository import (
    ArchivalRepository,
)


@pytest.fixture
def archival_env(tmp_path: Path):
    db_file = tmp_path / "test_archival.db"
    storage_dir = tmp_path / "storage"
    archives_dir = tmp_path / "archives"
    storage_dir.mkdir(parents=True, exist_ok=True)
    archives_dir.mkdir(parents=True, exist_ok=True)

    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)
    report_svc = ReportService(db_manager)
    arch_svc = ArchivalService(db_manager, storage_dir=str(storage_dir))
    rf_svc = RollForwardService(db_manager)
    backup_svc = BackupRestoreService(db_manager, storage_dir=str(storage_dir))

    firm = firm_svc.create_firm(CreateFirmDTO(name="National Audit LLP"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Apex Dynamics Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    # 1. Setup Risk and Substantive Procedure
    risk = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-REV-01",
            title="Revenue Cut-off Inaccuracy",
            category="Revenue",
            description="Risk of premature revenue recognition before delivery.",
            inherent_risk="High",
            control_risk="Medium",
        )
    )
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            risk_id=risk.id,
            procedure_code="PRC-REV-01",
            objective="Inspect sales invoices around balance sheet date for cut-off assertions.",
            procedure_type="Substantive Test of Detail",
            status="Completed",
        )
    )

    # 2. Setup Working Paper and Sign-Off
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-100",
            title="Revenue Cut-Off Testing",
            area="Revenue",
            preparer_id="Senior Auditor",
        )
    )
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Engagement Partner",
            user_role="Partner",
        )
    )

    # 3. Setup Approved Report
    tpls = report_svc.list_templates()
    rep = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng.id,
            template_id=tpls[0].id,
            title="Independent Auditor's Report FY 2025-26",
            generated_by="Engagement Partner",
        )
    )
    report_svc.approve_report(
        ApproveReportDTO(report_id=rep.id, approved_by="Engagement Partner", approver_role="Partner")
    )

    return {
        "db_manager": db_manager,
        "eng": eng,
        "risk": risk,
        "proc": proc,
        "wp": wp,
        "report": rep,
        "arch_svc": arch_svc,
        "rf_svc": rf_svc,
        "backup_svc": backup_svc,
        "matrix_svc": matrix_svc,
        "wp_svc": wp_svc,
        "archives_dir": archives_dir,
        "storage_dir": storage_dir,
    }


def test_archive_preservation_and_integrity(archival_env) -> None:
    """Verify archive freezes engagement, creates sealed package, and detects tampering."""
    env = archival_env
    arch_svc: ArchivalService = env["arch_svc"]
    eng = env["eng"]
    archives_dir = env["archives_dir"]

    archive = arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Engagement Partner",
            report_date="2026-03-31",
            output_dir=str(archives_dir),
        )
    )

    assert Path(archive.archive_path).exists()
    assert len(archive.sealed_content_hash) == 64
    assert arch_svc.get_engagement_status(eng.id) == "Archived"

    # Integrity verification must pass
    assert arch_svc.verify_archive_package(archive.archive_path) is True

    # Tamper test: Corrupting archive package must fail verification
    with open(archive.archive_path, "ab") as f:
        f.write(b"TAMPER_PAYLOAD")

    assert arch_svc.verify_archive_package(archive.archive_path) is False


def test_archived_engagement_read_only_immutability(archival_env) -> None:
    """Verify archived engagement blocks all mutations until authorized reopen."""
    env = archival_env
    arch_svc: ArchivalService = env["arch_svc"]
    matrix_svc: AuditMatrixService = env["matrix_svc"]
    wp_svc: WorkingPaperService = env["wp_svc"]
    eng = env["eng"]

    arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Engagement Partner",
            report_date="2026-03-31",
            output_dir=str(env["archives_dir"]),
        )
    )

    # 1. Attempting to create a working paper must be blocked
    with pytest.raises(EngagementLockedError):
        wp_svc.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=eng.id,
                index_reference="WP-ILLEGAL",
                title="Unauthorized Working Paper",
                area="Tax",
                preparer_id="Auditor",
            )
        )

    # 2. Attempting to create risk must be blocked
    with pytest.raises(EngagementLockedError):
        matrix_svc.create_risk(
            CreateRiskDTO(
                engagement_id=eng.id,
                risk_code="RSK-ILLEGAL",
                title="Unauthorized Risk",
                category="Tax",
                description="Illegal risk injection",
            )
        )

    # 3. Attempting to create procedure must be blocked
    with pytest.raises(EngagementLockedError):
        matrix_svc.create_procedure(
            CreateProcedureDTO(
                engagement_id=eng.id,
                procedure_code="PRC-ILLEGAL",
                objective="Illegal procedure",
            )
        )

    # 4. Attempting to create finding must be blocked
    with pytest.raises(EngagementLockedError):
        matrix_svc.create_finding(
            CreateFindingDTO(
                engagement_id=eng.id,
                title="Illegal Finding",
                description="Illegal finding injection",
            )
        )


def test_authorized_reopen_workflow(archival_env) -> None:
    """Verify RBAC on reopen (Partner only) and audit record logging."""
    env = archival_env
    arch_svc: ArchivalService = env["arch_svc"]
    eng = env["eng"]
    db_manager = env["db_manager"]

    arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Engagement Partner",
            report_date="2026-03-31",
            output_dir=str(env["archives_dir"]),
        )
    )

    # Non-partner role should be rejected
    with pytest.raises(PermissionDeniedError):
        arch_svc.reopen_engagement(
            ReopenEngagementDTO(
                engagement_id=eng.id,
                reopened_by="Senior Auditor",
                user_role="Senior",
                reason="Subsequent event discovery.",
            )
        )

    # Authorized partner succeeds
    arch_svc.reopen_engagement(
        ReopenEngagementDTO(
            engagement_id=eng.id,
            reopened_by="Senior Partner",
            user_role=RoleEnum.PARTNER,
            reason="NFRA Quality Review regulatory subpoena inquiry.",
        )
    )

    assert arch_svc.get_engagement_status(eng.id) == "Reopened"

    with db_manager.session_scope() as session:
        arch_repo = ArchivalRepository(session)
        reopens = arch_repo.list_reopen_records(eng.id)
        assert len(reopens) == 1
        assert reopens[0].reopened_by == "Senior Partner"
        assert "NFRA" in reopens[0].reason


def test_backup_restore_roundtrip(archival_env, tmp_path: Path) -> None:
    """Verify backup archive package can be restored and verified cleanly."""
    env = archival_env
    backup_svc: BackupRestoreService = env["backup_svc"]
    backup_file = tmp_path / "system_backup.zip"

    # Create backup package
    backup_path = backup_svc.create_backup(str(backup_file))
    assert Path(backup_path).exists()

    # Restore backup
    restored = backup_svc.restore_backup(backup_path)
    assert restored is True


def test_roll_forward_multi_category_decisions(archival_env) -> None:
    """Verify FY 2025-26 -> FY 2026-27 roll-forward with KEEP/UPDATE/REMOVE decisions and omission of CY testing."""
    env = archival_env
    arch_svc: ArchivalService = env["arch_svc"]
    rf_svc: RollForwardService = env["rf_svc"]
    eng = env["eng"]
    db_manager = env["db_manager"]

    # Seal prior year engagement
    arch_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Engagement Partner",
            report_date="2026-03-31",
            output_dir=str(env["archives_dir"]),
        )
    )

    # Execute Roll-Forward with custom decisions
    decisions = {
        "client_information": CarriedItemDecisionEnum.KEEP,
        "permanent_file": CarriedItemDecisionEnum.KEEP,
        "audit_program": CarriedItemDecisionEnum.UPDATE,
        "working_paper_structure": CarriedItemDecisionEnum.KEEP,
        "prior_year_findings": CarriedItemDecisionEnum.KEEP,
        "account_mappings": CarriedItemDecisionEnum.KEEP,
        "risk_templates": CarriedItemDecisionEnum.UPDATE,
        "methodology_references": CarriedItemDecisionEnum.KEEP,
    }

    new_eng = rf_svc.roll_forward_engagement(
        ExecuteRollForwardDTO(
            source_engagement_id=eng.id,
            target_financial_year="2026-27",
            performed_by="Audit Senior",
            category_decisions=decisions,
        )
    )

    assert new_eng.financial_year == "2026-27"
    assert new_eng.client_id == eng.client_id

    # Verify working papers in new engagement:
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        new_wps = wp_repo.list_for_engagement(new_eng.id)
        assert len(new_wps) == 1
        rolled_wp = new_wps[0]
        # Working paper status reset to DRAFT
        assert rolled_wp.status == WorkingPaperStatusEnum.DRAFT
        # Conclusion strictly NOT carried
        assert rolled_wp.conclusion == ""
        # Not locked
        assert rolled_wp.is_locked is False

        # Verify audit procedures in new engagement:
        matrix_repo = AuditMatrixRepository(session)
        new_procs = matrix_repo.list_procedures_for_engagement(new_eng.id)
        assert len(new_procs) == 1
        rolled_proc = new_procs[0]
        assert rolled_proc.status.value == "Not Started"
        assert rolled_proc.conclusion is None
        assert "Updated for FY 2026-27" in rolled_proc.objective

        # Verify roll forward record and content hash
        rf_repo = RollForwardRepository(session)
        rec = rf_repo.get_roll_forward_record(new_eng.id)
        assert rec is not None
        assert rec.source_fy == "2025-26"
        assert rec.target_fy == "2026-27"
        assert rec.decisions["audit_program"] == "UPDATE"
        assert len(rec.content_hash) == 64
        # Verify strict omissions
        assert "Current-Year Evidence" in rec.items_omitted
        assert "Current-Year Conclusions" in rec.items_omitted
        assert "Current-Year Testing" in rec.items_omitted
        assert "Current-Year Management Representations" in rec.items_omitted
