"""Application service for First-Class Audit Evidence, Provenance, Integrity, and Lifecycle."""

from pathlib import Path
from uuid import uuid4

from finauditpro.application.evidence_dtos import (
    CreateEvidenceDTO,
    EvidenceIntegrityReportDTO,
    EvidenceProvenanceDTO,
    LinkEvidenceDTO,
    UpdateEvidenceStatusDTO,
)
from finauditpro.application.security.engagement_lock_guard import assert_engagement_not_locked
from finauditpro.domain.audit_matrix_entities import (
    AuditEvidence,
    EvidenceStatusEnum,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.evidence_state_machine import (
    EvidenceStateMachine,
    calculate_stream_sha256,
)
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    EngagementRepository,
    WorkingPaperRepository,
)


class EvidenceService:
    """Service governing first-class audit evidence, cryptographic integrity, lifecycle, and provenance."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_evidence(self, dto: CreateEvidenceDTO) -> AuditEvidence:
        """Create new audit evidence with cryptographic SHA-256 hash and provenance tracking."""
        with self.db_manager.session_scope() as session:
            eng = EngagementRepository(session).get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)
            assert_engagement_not_locked(eng)

            matrix_repo = AuditMatrixRepository(session)
            content_hash = None
            if dto.file_path:
                content_hash = calculate_stream_sha256(dto.file_path)
                # Check for existing evidence with identical file and title (prevent silent overwrites)
                existing = matrix_repo.list_evidence_for_engagement(dto.engagement_id)
                for ex in existing:
                    if ex.file_path == dto.file_path and ex.title == dto.title and ex.content_hash == content_hash:
                        return ex

            ev_code = dto.evidence_code or f"EVD-{str(uuid4())[:6].upper()}"
            init_status = EvidenceStatusEnum.VALIDATED if content_hash else EvidenceStatusEnum.UPLOADED

            ev = AuditEvidence(
                engagement_id=dto.engagement_id,
                evidence_code=ev_code,
                title=dto.title,
                excerpt_or_reference=dto.excerpt_or_reference,
                source=dto.source,
                file_path=dto.file_path,
                content_hash=content_hash,
                version=1,
                document_type=dto.document_type,
                location=dto.location or (f"Page {dto.page_number}" if dto.page_number else None),
                page_number=dto.page_number,
                row_index=dto.row_index,
                procedure_id=dto.procedure_id,
                working_paper_id=dto.working_paper_id,
                finding_id=dto.finding_id,
                sample_ref=dto.sample_ref,
                test_execution_id=dto.test_execution_id,
                uploaded_by=dto.uploaded_by,
                status=init_status,
            )

            created = matrix_repo.add_evidence(ev)

            # Auto-link to working paper if provided
            if dto.working_paper_id:
                wp_repo = WorkingPaperRepository(session)
                wp_repo.add_link(str(uuid4()), dto.working_paper_id, "EVIDENCE", created.id)

            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditEvidence",
                    entity_id=created.id,
                    action="EVIDENCE_CREATED",
                    payload={"code": created.evidence_code, "hash": created.content_hash, "status": created.status.value},
                    user_id=dto.uploaded_by,
                )
            )
            return created

    def verify_integrity(self, evidence_id: str) -> EvidenceIntegrityReportDTO:
        """Verify SHA-256 cryptographic integrity of evidence file on disk against recorded hash."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            ev = matrix_repo.get_evidence_by_id(evidence_id)
            if not ev:
                raise EntityNotFoundError("AuditEvidence", evidence_id)

            if not ev.file_path:
                return EvidenceIntegrityReportDTO(
                    evidence_id=ev.id, title=ev.title, stored_hash=ev.content_hash,
                    actual_hash=None, is_valid=True, status="NO_PHYSICAL_FILE",
                    details="Evidence is metadata/reference only without standalone disk file.",
                )

            file_path = Path(ev.file_path)
            if not file_path.is_file():
                return EvidenceIntegrityReportDTO(
                    evidence_id=ev.id, title=ev.title, stored_hash=ev.content_hash,
                    actual_hash=None, is_valid=False, status="FILE_MISSING",
                    details=f"File not found on disk at path: {ev.file_path}",
                )

            actual_hash = calculate_stream_sha256(file_path)
            is_valid = (actual_hash == ev.content_hash)
            if not is_valid:
                AuditEventRepository(session).add(
                    AuditEvent(
                        id=str(uuid4()),
                        engagement_id=ev.engagement_id,
                        entity_name="AuditEvidence",
                        entity_id=ev.id,
                        action="EVIDENCE_TAMPERING_DETECTED",
                        payload={"stored": ev.content_hash, "actual": actual_hash, "file": ev.file_path},
                        user_id="SecurityMonitor",
                    )
                )

            return EvidenceIntegrityReportDTO(
                evidence_id=ev.id,
                title=ev.title,
                stored_hash=ev.content_hash,
                actual_hash=actual_hash,
                is_valid=is_valid,
                status="INTEGRITY_VERIFIED" if is_valid else "TAMPERING_DETECTED",
                details="Cryptographic hash matches stored baseline." if is_valid else "Hash mismatch! Evidence was altered on disk.",
            )

    def update_evidence_status(self, dto: UpdateEvidenceStatusDTO) -> AuditEvidence:
        """Update evidence status via domain state machine enforcing role-based permissions."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            ev = matrix_repo.get_evidence_by_id(dto.evidence_id)
            if not ev:
                raise EntityNotFoundError("AuditEvidence", dto.evidence_id)

            eng = EngagementRepository(session).get_by_id(ev.engagement_id)
            if eng:
                assert_engagement_not_locked(eng)

            new_status = EvidenceStateMachine.transition(ev.status, dto.target_status, dto.actor_role)
            ev.status = new_status
            if dto.review_notes is not None:
                ev.review_notes = dto.review_notes
            if dto.target_status in (EvidenceStatusEnum.REVIEWED, EvidenceStatusEnum.ACCEPTED, EvidenceStatusEnum.REJECTED):
                ev.reviewed_by = dto.actor

            updated = matrix_repo.update_evidence(ev)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=ev.engagement_id,
                    entity_name="AuditEvidence",
                    entity_id=updated.id,
                    action="EVIDENCE_STATUS_UPDATED",
                    payload={"new_status": updated.status.value, "role": dto.actor_role},
                    user_id=dto.actor,
                )
            )
            return updated

    def link_evidence(self, dto: LinkEvidenceDTO) -> AuditEvidence:
        """Associate evidence with procedure, sample, finding, or working paper."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            ev = matrix_repo.get_evidence_by_id(dto.evidence_id)
            if not ev:
                raise EntityNotFoundError("AuditEvidence", dto.evidence_id)

            eng = EngagementRepository(session).get_by_id(ev.engagement_id)
            if eng:
                assert_engagement_not_locked(eng)

            if dto.procedure_id:
                ev.procedure_id = dto.procedure_id
            if dto.working_paper_id:
                ev.working_paper_id = dto.working_paper_id
                WorkingPaperRepository(session).add_link(str(uuid4()), dto.working_paper_id, "EVIDENCE", ev.id)
            if dto.finding_id:
                ev.finding_id = dto.finding_id
            if dto.sample_ref:
                ev.sample_ref = dto.sample_ref

            if ev.status in (EvidenceStatusEnum.UPLOADED, EvidenceStatusEnum.VALIDATED):
                ev.status = EvidenceStatusEnum.LINKED

            updated = matrix_repo.update_evidence(ev)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=ev.engagement_id,
                    entity_name="AuditEvidence",
                    entity_id=updated.id,
                    action="EVIDENCE_LINKED",
                    payload={"procedure_id": dto.procedure_id, "wp_id": dto.working_paper_id, "sample": dto.sample_ref},
                    user_id=dto.actor,
                )
            )
            return updated

    def get_provenance(self, evidence_id: str) -> EvidenceProvenanceDTO:
        """Trace full audit provenance chain from Working Paper to Procedure, Sample, Evidence, and Page."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            wp_repo = WorkingPaperRepository(session)
            ev = matrix_repo.get_evidence_by_id(evidence_id)
            if not ev:
                raise EntityNotFoundError("AuditEvidence", evidence_id)

            wp = wp_repo.get_by_id(ev.working_paper_id) if ev.working_paper_id else None
            proc = matrix_repo.get_procedure_by_id(ev.procedure_id) if ev.procedure_id else None
            finding = matrix_repo.get_finding_by_id(ev.finding_id) if ev.finding_id else None

            # Build readable provenance path
            parts = []
            if wp:
                parts.append(wp.index_reference)
            if proc:
                parts.append(f"Procedure {proc.procedure_code}")
            if ev.sample_ref:
                parts.append(f"Sample {ev.sample_ref}")
            parts.append(f"Evidence {ev.evidence_code or ev.id}")
            if ev.location or ev.page_number:
                parts.append(ev.location or f"Page {ev.page_number}")

            provenance_path = " → ".join(parts)
            integrity = self.verify_integrity(ev.id)

            return EvidenceProvenanceDTO(
                evidence=ev,
                provenance_path=provenance_path,
                working_paper=wp,
                procedure=proc,
                finding=finding,
                sample_ref=ev.sample_ref,
                document_location=ev.location,
                hash_verified=integrity.is_valid,
            )

    def list_evidence_for_engagement(self, engagement_id: str) -> list[AuditEvidence]:
        with self.db_manager.session_scope() as session:
            return AuditMatrixRepository(session).list_evidence_for_engagement(engagement_id)

    def detect_tampering_for_engagement(self, engagement_id: str) -> list[EvidenceIntegrityReportDTO]:
        """Audit all evidence files across the engagement and report any tampered or modified files."""
        items = self.list_evidence_for_engagement(engagement_id)
        return [self.verify_integrity(item.id) for item in items if item.file_path]
