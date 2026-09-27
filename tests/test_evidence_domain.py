"""Tests for First-Class Audit Evidence Domain, Lifecycle, Provenance, Integrity, Permissions, and Navigation."""

import os
from pathlib import Path
import pytest

from finauditpro.application.dtos import CreateEngagementDTO
from finauditpro.application.evidence_dtos import (
    CreateEvidenceDTO,
    LinkEvidenceDTO,
    UpdateEvidenceStatusDTO,
)
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.evidence_service import EvidenceService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditProcedure,
    AuditRisk,
    EvidenceStatusEnum,
)
from finauditpro.domain.entities import EngagementStatusEnum
from finauditpro.domain.exceptions import (
    EngagementLockedError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ValidationError,
)
from finauditpro.domain.working_paper_entities import FileCategoryEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import (
    Base,
    ClientModel,
    FirmModel,
)
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
)


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "test_evidence_domain.db"
    db_manager = DatabaseManager(f"sqlite:///{db_file}")
    with db_manager.engine.begin() as conn:
        Base.metadata.create_all(conn)

    with db_manager.session_scope() as session:
        session.add(FirmModel(id="firm-01", name="S. K. & Associates", registration_number="FRN-123456"))
        session.add(ClientModel(id="client-tatasteel", firm_id="firm-01", name="Tata Steel Limited", pan="AAACT1234A"))

    return db_manager


@pytest.fixture
def active_engagement(test_db: DatabaseManager) -> str:
    eng_service = EngagementService(test_db)
    eng = eng_service.create_engagement(
        CreateEngagementDTO(
            firm_id="firm-01",
            client_id="client-tatasteel",
            engagement_name="Statutory Audit FY 2025-26",
            financial_year="2025-26",
            engagement_type="STATUTORY_AUDIT",
            partner="CA Rajesh Sharma",
            manager="CA Priya Mehta",
            team_members=["CA Rajesh Sharma", "CA Priya Mehta", "Auditor"],
        )
    )
    return eng.id


def test_evidence_creation_and_provenance_chain(test_db: DatabaseManager, active_engagement: str, tmp_path: Path):
    """Test creating evidence with full metadata and verifying canonical provenance path:
    WP-REV-001 -> Procedure REV-CUTOFF-01 -> Sample INV-29182 -> Evidence EVD-0092 -> PDF page 4.
    """
    # 1. Setup Working Paper & Procedure
    wp_service = WorkingPaperService(test_db)
    wp = wp_service.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=active_engagement,
            index_reference="WP-REV-001",
            title="Revenue Cut-off Testing Schedule",
            area="Revenue",
            file_category=FileCategoryEnum.CURRENT_FILE,
            preparer_id="Auditor",
        )
    )

    with test_db.session_scope() as session:
        matrix_repo = AuditMatrixRepository(session)
        proc = matrix_repo.add_procedure(
            AuditProcedure(
                engagement_id=active_engagement,
                procedure_code="REV-CUTOFF-01",
                objective="Test cut-off around balance sheet date.",
                account_area="Revenue",
                assertions=[AssertionEnum.CUT_OFF],
            )
        )

    # 2. Create sample PDF document file
    pdf_file = tmp_path / "invoice_29182.pdf"
    pdf_file.write_bytes(b"%PDF-1.5 Sample Tax Invoice 29182 for Revenue Cut-off Verification")

    # 3. Create Evidence
    ev_service = EvidenceService(test_db)
    ev = ev_service.create_evidence(
        CreateEvidenceDTO(
            engagement_id=active_engagement,
            evidence_code="EVD-0092",
            title="Tax Invoice & e-Way Bill for Sample #29182",
            excerpt_or_reference="Tax Invoice #29182 dated 29-Mar-2026 for INR 4,50,000",
            file_path=str(pdf_file),
            source="Vendor e-Way Portal & ERP",
            document_type="Tax Invoice / Transporter Bilty",
            location="PDF page 4",
            page_number=4,
            procedure_id=proc.id,
            working_paper_id=wp.id,
            sample_ref="INV-29182",
            uploaded_by="Junior Auditor",
        )
    )

    # Verify evidence fields
    assert ev.id is not None
    assert ev.evidence_code == "EVD-0092"
    assert ev.engagement_id == active_engagement
    assert ev.file_path == str(pdf_file)
    assert ev.content_hash is not None
    assert len(ev.content_hash) == 64  # SHA-256 hex
    assert ev.version == 1
    assert ev.page_number == 4
    assert ev.related_procedure == proc.id
    assert ev.related_working_paper == wp.id
    assert ev.sample_ref == "INV-29182"
    assert ev.status == EvidenceStatusEnum.VALIDATED

    # Verify provenance DTO
    prov = ev_service.get_provenance(ev.id)
    assert prov.working_paper.id == wp.id
    assert prov.procedure.id == proc.id
    assert prov.sample_ref == "INV-29182"
    assert prov.hash_verified is True
    assert "WP-REV-001" in prov.provenance_path
    assert "REV-CUTOFF-01" in prov.provenance_path
    assert "INV-29182" in prov.provenance_path
    assert "EVD-0092" in prov.provenance_path
    assert "PDF page 4" in prov.provenance_path


def test_evidence_integrity_and_tamper_detection(test_db: DatabaseManager, active_engagement: str, tmp_path: Path):
    """Test cryptographic SHA-256 baseline calculation and detection of on-disk file alterations."""
    doc_file = tmp_path / "bank_confirmation.pdf"
    doc_file.write_bytes(b"Original Bank Confirmation Balance = INR 50,00,000")

    ev_service = EvidenceService(test_db)
    ev = ev_service.create_evidence(
        CreateEvidenceDTO(
            engagement_id=active_engagement,
            title="State Bank of India Direct Confirmation",
            excerpt_or_reference="Account No 12345678 balance verification",
            file_path=str(doc_file),
            uploaded_by="Auditor",
        )
    )

    # 1. Initial check - intact
    report1 = ev_service.verify_integrity(ev.id)
    assert report1.is_valid is True
    assert report1.status == "INTEGRITY_VERIFIED"
    assert report1.stored_hash == report1.actual_hash

    # 2. Simulate malicious disk modification / alteration
    doc_file.write_bytes(b"Tampered Bank Confirmation Balance = INR 90,00,000")

    # 3. Subsequent check - detects tampering immediately
    report2 = ev_service.verify_integrity(ev.id)
    assert report2.is_valid is False
    assert report2.status == "TAMPERING_DETECTED"
    assert report2.actual_hash != report2.stored_hash

    # 4. Verify tampering security event logged
    with test_db.session_scope() as session:
        events = AuditEventRepository(session).list_for_engagement(active_engagement)
    actions = [e.action for e in events]
    assert "EVIDENCE_TAMPERING_DETECTED" in actions


def test_evidence_lifecycle_state_machine_and_permissions(test_db: DatabaseManager, active_engagement: str):
    """Test explicit lifecycle transitions (UPLOADED -> VALIDATED -> LINKED -> REVIEWED -> ACCEPTED) and role restrictions."""
    ev_service = EvidenceService(test_db)
    ev = ev_service.create_evidence(
        CreateEvidenceDTO(
            engagement_id=active_engagement,
            title="Fixed Asset Title Deed Copy",
            excerpt_or_reference="Title deed for Land & Building Plot 42",
            uploaded_by="Junior Auditor",
        )
    )

    assert ev.status == EvidenceStatusEnum.UPLOADED

    # 1. Transition to VALIDATED
    ev = ev_service.update_evidence_status(
        UpdateEvidenceStatusDTO(
            evidence_id=ev.id,
            target_status=EvidenceStatusEnum.VALIDATED,
            actor="Auditor",
            actor_role="Auditor",
        )
    )
    assert ev.status == EvidenceStatusEnum.VALIDATED

    # 2. Transition to LINKED via link_evidence
    ev = ev_service.link_evidence(
        LinkEvidenceDTO(
            evidence_id=ev.id,
            sample_ref="FA-PLOT-42",
            actor="Auditor",
        )
    )
    assert ev.status == EvidenceStatusEnum.LINKED

    # 3. Transition to REVIEWED
    ev = ev_service.update_evidence_status(
        UpdateEvidenceStatusDTO(
            evidence_id=ev.id,
            target_status=EvidenceStatusEnum.REVIEWED,
            actor="CA Priya Mehta",
            actor_role="Manager",
            review_notes="Title deed verified with Registrar records.",
        )
    )
    assert ev.status == EvidenceStatusEnum.REVIEWED

    # 4. Junior Auditor attempting to mark ACCEPTED must be rejected (Permission Enforcement)
    with pytest.raises(ValidationError):
        ev_service.update_evidence_status(
            UpdateEvidenceStatusDTO(
                evidence_id=ev.id,
                target_status=EvidenceStatusEnum.ACCEPTED,
                actor="Junior Auditor",
                actor_role="Junior Assistant",
            )
        )

    # 5. Partner or Manager approving evidence succeeds
    ev = ev_service.update_evidence_status(
        UpdateEvidenceStatusDTO(
            evidence_id=ev.id,
            target_status=EvidenceStatusEnum.ACCEPTED,
            actor="CA Rajesh Sharma",
            actor_role="Partner",
            review_notes="Accepted as conclusive audit evidence for Land title.",
        )
    )
    assert ev.status == EvidenceStatusEnum.ACCEPTED

    # 6. Invalid transition: ACCEPTED directly back to UPLOADED must fail
    with pytest.raises(InvalidStateTransitionError):
        ev_service.update_evidence_status(
            UpdateEvidenceStatusDTO(
                evidence_id=ev.id,
                target_status=EvidenceStatusEnum.UPLOADED,
                actor="CA Rajesh Sharma",
                actor_role="Partner",
            )
        )


def test_engagement_lock_prevents_evidence_mutation(test_db: DatabaseManager, active_engagement: str):
    """Test that locking/archiving an engagement prevents adding or modifying evidence."""
    eng_service = EngagementService(test_db)
    ev_service = EvidenceService(test_db)

    ev = ev_service.create_evidence(
        CreateEvidenceDTO(
            engagement_id=active_engagement,
            title="Board Resolution Excerpt",
            excerpt_or_reference="Resolution authorizing borrowings",
        )
    )

    # Lock the engagement
    eng_service.lock_engagement(active_engagement, locked_by="Engagement Partner")

    # Creating evidence on locked engagement fails
    with pytest.raises(EngagementLockedError):
        ev_service.create_evidence(
            CreateEvidenceDTO(
                engagement_id=active_engagement,
                title="New Evidence Post Lock",
                excerpt_or_reference="Testing locked guard",
            )
        )

    # Updating evidence on locked engagement fails
    with pytest.raises(EngagementLockedError):
        ev_service.update_evidence_status(
            UpdateEvidenceStatusDTO(
                evidence_id=ev.id,
                target_status=EvidenceStatusEnum.VALIDATED,
            )
        )


def test_bidirectional_evidence_navigation(test_db: DatabaseManager, active_engagement: str):
    """Test navigating 2-way between Evidence <-> Working Paper, Evidence <-> Procedure, Evidence <-> Sample."""
    wp_service = WorkingPaperService(test_db)
    wp = wp_service.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=active_engagement,
            index_reference="WP-BNK-01",
            title="Bank Reconciliations",
            area="Cash & Bank",
            preparer_id="Auditor",
        )
    )

    with test_db.session_scope() as session:
        matrix_repo = AuditMatrixRepository(session)
        proc = matrix_repo.add_procedure(
            AuditProcedure(
                engagement_id=active_engagement,
                procedure_code="PROC-BNK-01",
                objective="Inspect BRS clearance.",
                account_area="Cash & Bank",
            )
        )

    ev_service = EvidenceService(test_db)
    ev = ev_service.create_evidence(
        CreateEvidenceDTO(
            engagement_id=active_engagement,
            title="HDFC Bank Statement March 2026",
            excerpt_or_reference="Closing balance INR 25,10,000",
            working_paper_id=wp.id,
            procedure_id=proc.id,
            sample_ref="BNK-HDFC-01",
        )
    )

    trace_service = TraceabilityService(test_db)

    # Forward navigation
    wp_evs = trace_service.get_evidence_for_working_paper(active_engagement, wp.id)
    assert any(e.id == ev.id for e in wp_evs)

    proc_evs = trace_service.get_evidence_for_procedure(active_engagement, proc.id)
    assert any(e.id == ev.id for e in proc_evs)

    sample_evs = trace_service.get_evidence_for_sample(active_engagement, "BNK-HDFC-01")
    assert any(e.id == ev.id for e in sample_evs)

    # Reverse navigation
    ev_wps = trace_service.get_working_papers_for_evidence(active_engagement, ev.id)
    assert len(ev_wps) == 1
    assert ev_wps[0].id == wp.id

    ev_procs = trace_service.get_procedures_for_evidence(active_engagement, ev.id)
    assert len(ev_procs) == 1
    assert ev_procs[0].id == proc.id


def test_large_document_streaming_hash_integrity(test_db: DatabaseManager, active_engagement: str, tmp_path: Path):
    """Test chunked streaming SHA-256 on a large 10 MB document file without loading it entirely into memory."""
    large_file = tmp_path / "large_annual_report.pdf"
    # Write 10 MB of deterministic chunked data
    chunk = b"A" * 65536
    with large_file.open("wb") as f:
        for _ in range(160):  # 160 * 64 KB = 10 MB
            f.write(chunk)

    ev_service = EvidenceService(test_db)
    ev = ev_service.create_evidence(
        CreateEvidenceDTO(
            engagement_id=active_engagement,
            title="Large Annual Report Document (10 MB)",
            excerpt_or_reference="Complete statutory financial statement and notes",
            file_path=str(large_file),
            document_type="Financial Statements / Annual Report",
            uploaded_by="Auditor",
        )
    )

    assert ev.content_hash is not None
    assert len(ev.content_hash) == 64

    # Verify integrity report passes
    report = ev_service.verify_integrity(ev.id)
    assert report.is_valid is True
    assert report.status == "INTEGRITY_VERIFIED"
    assert report.actual_hash == ev.content_hash
