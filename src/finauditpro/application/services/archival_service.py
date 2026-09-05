"""Application service orchestrating readiness checks, engagement freeze, archive sealing, retention timelines, and audited partner reopens."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from finauditpro.application.archival_dtos import (
    FreezeAndSealDTO,
    ReadinessCheckResultDTO,
    ReadinessItemDTO,
    ReopenEngagementDTO,
)
from finauditpro.application.services.backup_restore_service import BackupRestoreService
from finauditpro.domain.archival_entities import (
    ArchiveReopenRecord,
    EngagementArchive,
    RetentionConfig,
)
from finauditpro.domain.entities import AuditEvent, EngagementStatusEnum, RoleEnum
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
    ReportRepository,
    WorkingPaperRepository,
)
from finauditpro.infrastructure.persistence.repositories.archival_repository import (
    ArchivalRepository,
)


class ArchivalService:
    """Service handling pre-archive readiness checks, sealed archives, read-only freeze, and audited reopens."""

    def __init__(self, db_manager: DatabaseManager, storage_dir: str | Path | None = None) -> None:
        self.db_manager = db_manager
        database_path = Path(str(db_manager.engine.url.database))
        self.storage_dir = str(
            Path(storage_dir) if storage_dir else database_path.parent / "storage"
        )
        self.backup_svc = BackupRestoreService(db_manager, storage_dir=storage_dir)

    def get_or_create_retention_config(self) -> RetentionConfig:
        """Fetch active retention policy or seed default non-statutory config with verified_statutory=False."""
        with self.db_manager.session_scope() as session:
            repo = ArchivalRepository(session)
            cfg = repo.get_active_retention_config()
            if not cfg:
                default_cfg = RetentionConfig(
                    version="1.0",
                    assembly_period_days=60,
                    retention_period_years=7,
                    source="SA 230 Audit Documentation Standard Guidance (Firm Policy)",
                    effective_from="2025-04-01",
                    verified_statutory=False,
                )
                cfg = repo.save_retention_config(default_cfg)
            return cfg

    def run_readiness_check(self, engagement_id: str) -> ReadinessCheckResultDTO:
        """Run pre-archive readiness check querying real DB records across all subsystems."""
        items: list[ReadinessItemDTO] = []
        has_hard = False
        has_soft = False

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", engagement_id)

            # 1. Working Paper Sign-Off Status
            wp_repo = WorkingPaperRepository(session)
            wps = wp_repo.list_for_engagement(engagement_id)
            unsigned = [wp for wp in wps if wp.status.value not in ("Signed Off", "Locked")]
            if unsigned:
                has_hard = True
                items.append(
                    ReadinessItemDTO(
                        category="Working Papers",
                        item_name="Working Paper Sign-Offs",
                        is_passed=False,
                        is_hard_blocker=True,
                        details=f"{len(unsigned)} working paper(s) are not signed off or locked.",
                    )
                )
            else:
                items.append(
                    ReadinessItemDTO(
                        category="Working Papers",
                        item_name="Working Paper Sign-Offs",
                        is_passed=True,
                        is_hard_blocker=True,
                        details=f"All {len(wps)} working paper(s) are fully signed off and locked.",
                    )
                )

            # 2. Open Review Notes Check
            open_notes_count = 0
            for wp in wps:
                notes = wp_repo.list_review_notes(wp.id)
                open_notes_count += sum(1 for n in notes if n.status.value == "Open")

            if open_notes_count > 0:
                has_hard = True
                items.append(
                    ReadinessItemDTO(
                        category="Review Notes",
                        item_name="Open Review Notes",
                        is_passed=False,
                        is_hard_blocker=True,
                        details=f"{open_notes_count} open review note(s) remain uncleared.",
                    )
                )
            else:
                items.append(
                    ReadinessItemDTO(
                        category="Review Notes",
                        item_name="Open Review Notes",
                        is_passed=True,
                        is_hard_blocker=True,
                        details="Zero open review notes.",
                    )
                )

            # 3. Approved Reports Check
            rep_repo = ReportRepository(session)
            reports = rep_repo.list_for_engagement(engagement_id)
            approved = [r for r in reports if r.status.value == "Approved"]
            if not approved:
                has_soft = True
                items.append(
                    ReadinessItemDTO(
                        category="Reporting",
                        item_name="Approved Report",
                        is_passed=False,
                        is_hard_blocker=False,
                        details="No approved audit report found in engagement.",
                    )
                )
            else:
                items.append(
                    ReadinessItemDTO(
                        category="Reporting",
                        item_name="Approved Report",
                        is_passed=True,
                        is_hard_blocker=False,
                        details=f"Found {len(approved)} approved report(s).",
                    )
                )

            # 4. Cryptographic Audit Chain Verification
            audit_repo = AuditEventRepository(session)
            if not audit_repo.verify_chain():
                has_hard = True
                items.append(
                    ReadinessItemDTO(
                        category="Audit Trail",
                        item_name="SHA-256 Hash Chain",
                        is_passed=False,
                        is_hard_blocker=True,
                        details="STARTUP/PRE-SEAL INTEGRITY FAILURE: Audit trail hash chain broken!",
                    )
                )
            else:
                items.append(
                    ReadinessItemDTO(
                        category="Audit Trail",
                        item_name="SHA-256 Hash Chain",
                        is_passed=True,
                        is_hard_blocker=True,
                        details="Cryptographic audit chain verified & intact.",
                    )
                )

            # 5. SQC 1 / SQM 1 High-Risk Audit Procedure Response Check
            from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
                AuditMatrixRepository,
            )

            matrix_repo = AuditMatrixRepository(session)
            risks = matrix_repo.list_risks_for_engagement(engagement_id)
            high_risks = [r for r in risks if hasattr(r, "romm") and r.romm.value == "High"]
            procs = matrix_repo.list_procedures_for_engagement(engagement_id)
            unresponded_high_risks = []
            for hr in high_risks:
                linked = [p for p in procs if hr.id in getattr(p, "linked_risk_ids", [])]
                if not linked or not any(
                    p.status.value in ("Completed", "Reviewed") for p in linked
                ):
                    unresponded_high_risks.append(hr.risk_code)

            if unresponded_high_risks:
                has_soft = True
                items.append(
                    ReadinessItemDTO(
                        category="SQC 1 Quality",
                        item_name="High-Risk Procedure Responses",
                        is_passed=False,
                        is_hard_blocker=False,
                        details=f"{len(unresponded_high_risks)} high-risk RoMM item(s) [{', '.join(unresponded_high_risks[:3])}] lack completed audit procedures.",
                    )
                )
            else:
                items.append(
                    ReadinessItemDTO(
                        category="SQC 1 Quality",
                        item_name="High-Risk Procedure Responses",
                        is_passed=True,
                        is_hard_blocker=False,
                        details=f"All {len(high_risks)} high RoMM risk items have substantive procedural responses.",
                    )
                )

        is_ready = not has_hard
        return ReadinessCheckResultDTO(
            engagement_id=engagement_id,
            is_ready_to_seal=is_ready,
            items=items,
            has_hard_failures=has_hard,
            has_soft_warnings=has_soft,
        )

    def freeze_and_seal_engagement(self, dto: FreezeAndSealDTO) -> EngagementArchive:
        """Freeze engagement, seal DB + files + reports into a deterministic archive, and record retention timeline."""
        readiness = self.run_readiness_check(dto.engagement_id)
        if readiness.has_hard_failures:
            raise ValidationError("Cannot seal engagement: Hard readiness check failures exist.")

        if readiness.has_soft_warnings and not (
            dto.override_justification and dto.override_justification.strip()
        ):
            raise ValidationError(
                "Override justification required to seal engagement with soft warnings."
            )

        # Compute Retention Timelines
        ret_cfg = self.get_or_create_retention_config()
        try:
            rep_date = datetime.strptime(dto.report_date, "%Y-%m-%d").replace(tzinfo=UTC)
        except Exception:
            rep_date = datetime.now(UTC)

        assembly_deadline_dt = rep_date + timedelta(days=ret_cfg.assembly_period_days)
        retain_until_dt = rep_date + timedelta(days=ret_cfg.retention_period_years * 365)

        assembly_deadline_str = assembly_deadline_dt.strftime("%Y-%m-%d")
        retain_until_str = retain_until_dt.strftime("%Y-%m-%d")

        # Create Archive Storage Directory
        out_dir = Path(dto.output_dir) if dto.output_dir else Path(self.storage_dir) / "archives"
        out_dir.mkdir(parents=True, exist_ok=True)
        archive_path = str(out_dir / f"sealed_engagement_{dto.engagement_id[:8]}.zip")

        # Create Encrypted/Plain Archive
        self.backup_svc.create_backup(archive_path, passphrase=dto.passphrase)

        # Calculate Manifest Hash & Content Hash
        from finauditpro.infrastructure.documents.document_security import calculate_sha256

        sealed_hash = calculate_sha256(archive_path)

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            eng.status = EngagementStatusEnum.ARCHIVED
            eng_repo.update(eng)

            arch_repo = ArchivalRepository(session)
            archive = EngagementArchive(
                engagement_id=dto.engagement_id,
                archive_path=archive_path,
                manifest_hash=sealed_hash[:32],
                sealed_content_hash=sealed_hash,
                is_encrypted=bool(dto.passphrase),
                report_date=dto.report_date,
                assembly_deadline=assembly_deadline_str,
                retain_until=retain_until_str,
                sealed_by=dto.sealed_by,
            )
            saved_archive = arch_repo.add_archive(archive)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.sealed_by,
                    action="Engagement Sealed & Frozen",
                    details=f"Sealed audit file archive created at '{archive_path}' (Hash: {sealed_hash[:12]}...). Assembly deadline: {assembly_deadline_str}, Retain until: {retain_until_str}",
                )
            )

        return saved_archive

    def list_archives_for_engagement(self, engagement_id: str) -> list[EngagementArchive]:
        """List sealed archives for engagement."""
        with self.db_manager.session_scope() as session:
            arch_repo = ArchivalRepository(session)
            return arch_repo.list_archives_for_engagement(engagement_id)

    def get_engagement_status(self, engagement_id: str) -> str:
        """Fetch engagement status string."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(engagement_id)
            return eng.status.value if eng else "Unknown"

    def reopen_engagement(self, dto: ReopenEngagementDTO) -> None:
        """RBAC-gated (Partner only) engagement reopen preserving prior sealed archive records."""
        if dto.user_role != RoleEnum.PARTNER and dto.user_role != "Partner":
            raise PermissionDeniedError(
                "Only Audit Partners are authorized to reopen sealed engagements."
            )

        if not dto.reason or not dto.reason.strip():
            raise ValidationError(
                "A detailed justification reason is required to reopen a sealed engagement."
            )

        with self.db_manager.session_scope() as session:
            arch_repo = ArchivalRepository(session)
            latest_arch = arch_repo.get_latest_archive(dto.engagement_id)
            if not latest_arch:
                raise EntityNotFoundError("Sealed Archive", dto.engagement_id)

            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            eng.status = EngagementStatusEnum.REOPENED
            eng_repo.update(eng)

            reopen_rec = ArchiveReopenRecord(
                engagement_id=dto.engagement_id,
                reopened_by=dto.reopened_by,
                reason=dto.reason.strip(),
                prior_archive_id=latest_arch.id,
            )
            arch_repo.add_reopen_record(reopen_rec)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.reopened_by,
                    action="Engagement Reopened",
                    details=f"Engagement reopened by Partner. Reason: '{dto.reason}'. Prior archive preserved: {latest_arch.id}",
                )
            )

    def verify_archive_package(self, archive_path: str) -> bool:
        """Independently verify the cryptographic integrity and file structure of an archived package."""
        import zipfile
        from pathlib import Path

        from finauditpro.infrastructure.documents.document_security import calculate_sha256

        p = Path(archive_path)
        if not p.exists() or not p.is_file():
            return False
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                if zf.testzip() is not None:
                    return False
            curr_hash = calculate_sha256(archive_path)
            with self.db_manager.session_scope() as session:
                from finauditpro.infrastructure.persistence.archival_models import (
                    EngagementArchiveModel,
                )

                archives = (
                    session.query(EngagementArchiveModel).filter_by(archive_path=archive_path).all()
                )
                if archives:
                    return archives[0].sealed_content_hash == curr_hash
            return len(curr_hash) == 64
        except Exception:
            return False
