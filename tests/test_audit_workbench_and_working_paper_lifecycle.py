"""Comprehensive tests for Working Paper state machine, canonical audit graph integration, and 3-pane workbench data."""

import pytest

from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    ReopenWorkingPaperDTO,
    RespondReviewNoteDTO,
    SignOffDTO,
)
from finauditpro.domain.audit_execution_entities import AuditException, AuditSampleItemTest, TestExecution
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    RiskSeverityEnum,
)
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.working_paper_entities import (
    ReviewNoteStatusEnum,
    SignOffLevelEnum,
    WorkingPaper,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import AuditMatrixRepository
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import CoreAuditEngineRepository


@pytest.fixture
def workbench_env(tmp_path):
    db_file = tmp_path / "test_workbench.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Workbench CA & Co."))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Apex Industries Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    return eng, wp_svc, matrix_svc, db_manager


def test_working_paper_full_canonical_lifecycle_and_preconditions(workbench_env) -> None:
    """Verify full lifecycle: DRAFT -> PREPARED -> SUBMITTED -> UNDER REVIEW -> RETURNED -> RESUBMITTED -> APPROVED -> LOCKED."""
    eng, wp_svc, matrix_svc, db_manager = workbench_env

    # 1. DRAFT
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-01",
            title="Revenue Cut-off Testing",
            area="Revenue",
            preparer_id="Preparer User",
        )
    )
    assert wp.status == WorkingPaperStatusEnum.DRAFT
    assert wp.version == 1
    assert not wp.is_locked

    # 2. PREPARED
    wp_prepared = wp_svc.prepare_working_paper(wp.id, preparer_id="Preparer User")
    assert wp_prepared.status == WorkingPaperStatusEnum.PREPARED

    # 3. SUBMITTED
    wp_submitted = wp_svc.submit_for_review(wp.id, submitter_id="Preparer User")
    assert wp_submitted.status == WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW

    # 4. UNDER REVIEW
    wp_under_review = wp_svc.start_review(wp.id, reviewer_id="Senior Reviewer")
    assert wp_under_review.status == WorkingPaperStatusEnum.UNDER_REVIEW

    # 5. RETURNED
    wp_returned = wp_svc.return_working_paper(wp.id, reviewer_id="Senior Reviewer")
    assert wp_returned.status == WorkingPaperStatusEnum.RETURNED

    # 6. RESUBMITTED
    wp_resubmitted = wp_svc.submit_for_review(wp.id, submitter_id="Preparer User")
    assert wp_resubmitted.status == WorkingPaperStatusEnum.RESUBMITTED

    # Under Review again
    wp_under_review2 = wp_svc.start_review(wp.id, reviewer_id="Senior Reviewer")
    assert wp_under_review2.status == WorkingPaperStatusEnum.UNDER_REVIEW

    # 7. APPROVED (Precondition: No open review notes)
    wp_approved = wp_svc.approve_working_paper(wp.id, approver_id="Senior Reviewer")
    assert wp_approved.status == WorkingPaperStatusEnum.APPROVED

    # 8. LOCKED
    wp_locked = wp_svc.lock_working_paper(wp.id, locker_id="Partner Lead")
    assert wp_locked.status == WorkingPaperStatusEnum.LOCKED
    assert wp_locked.is_locked
    assert wp_locked.content_hash is not None


def test_approval_blocked_when_open_review_notes_remain(workbench_env) -> None:
    """Approval and Sign-off MUST be blocked when blocking review notes remain."""
    eng, wp_svc, matrix_svc, db_manager = workbench_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-PAY-01",
            title="Purchases Vouching",
            area="Purchases",
            preparer_id="Associate",
        )
    )
    wp_svc.prepare_working_paper(wp.id, preparer_id="Associate")
    wp_svc.submit_for_review(wp.id, submitter_id="Associate")
    wp_svc.start_review(wp.id, reviewer_id="Manager")

    # Raise an open review note
    note = wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="Manager",
            note_text="Missing 3 vendor invoice attachments for sample batch 4.",
        )
    )
    assert note.status == ReviewNoteStatusEnum.OPEN

    # Attempt to approve -> MUST fail
    with pytest.raises(ValidationError) as exc_info:
        wp_svc.approve_working_paper(wp.id, approver_id="Manager")
    assert "open review notes" in str(exc_info.value).lower()

    # Attempt to sign off -> MUST fail
    with pytest.raises(ValidationError) as exc_info2:
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id="Manager",
                user_role="Manager",
            )
        )
    assert "open review notes" in str(exc_info2.value).lower()

    # Respond to review note
    wp_svc.respond_review_note(
        RespondReviewNoteDTO(
            review_note_id=note.id,
            response_text="Uploaded invoices INV-101 to INV-103.",
            responder="Associate",
        )
    )

    # Still not cleared -> Approval still blocked
    with pytest.raises(ValidationError):
        wp_svc.approve_working_paper(wp.id, approver_id="Manager")

    # Clear review note
    wp_svc.clear_review_note(
        ClearReviewNoteDTO(
            review_note_id=note.id,
            reviewer="Manager",
        )
    )

    # Now approval succeeds
    approved_wp = wp_svc.approve_working_paper(wp.id, approver_id="Manager")
    assert approved_wp.status == WorkingPaperStatusEnum.APPROVED


def test_locking_enforced_at_domain_and_application_layer(workbench_env) -> None:
    """Locking must prevent any modification at domain and application layers."""
    eng, wp_svc, matrix_svc, db_manager = workbench_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-FA-01",
            title="Fixed Asset Additions",
            area="Fixed Assets",
            preparer_id="Associate",
        )
    )
    wp_svc.prepare_working_paper(wp.id, preparer_id="Associate")
    wp_svc.submit_for_review(wp.id, submitter_id="Associate")
    wp_svc.start_review(wp.id, reviewer_id="Manager")
    wp_svc.approve_working_paper(wp.id, approver_id="Manager")
    locked_wp = wp_svc.lock_working_paper(wp.id, locker_id="Partner")
    assert locked_wp.is_locked

    # Application layer edit attempt must fail
    with pytest.raises(ValidationError) as exc_edit:
        wp_svc.update_working_paper_content(
            wp_id=wp.id,
            title="Attempted Mod",
            area="Fixed Assets",
            conclusion="Tampered conclusion",
            sections_list=[],
            editor_id="Associate",
        )
    assert "locked" in str(exc_edit.value).lower()

    # Application layer sign off on locked paper must fail
    with pytest.raises(ValidationError):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="Partner",
                user_role="Partner",
            )
        )

    # Domain entity direct transition attempt must fail
    with pytest.raises(ValidationError):
        locked_wp.transition_to(WorkingPaperStatusEnum.DRAFT)


def test_reopening_creates_new_version_and_preserves_reconstructable_snapshots(workbench_env) -> None:
    """Reopening increments version (N -> N+1) and previous versions remain reconstructable."""
    eng, wp_svc, matrix_svc, db_manager = workbench_env

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-TAX-01",
            title="Statutory Tax Dues",
            area="Statutory Dues",
            preparer_id="Associate",
        )
    )
    wp_svc.update_working_paper_content(
        wp_id=wp.id,
        title="Statutory Tax Dues v1",
        area="Statutory Dues",
        conclusion="V1 conclusion: No major tax liabilities observed.",
        sections_list=[{"title": "Work Done v1", "content_markdown": "Tested GSTR-3B filings."}],
        editor_id="Associate",
    )
    wp_svc.prepare_working_paper(wp.id, preparer_id="Associate")
    wp_svc.submit_for_review(wp.id, submitter_id="Associate")
    wp_svc.start_review(wp.id, reviewer_id="Manager")
    wp_svc.approve_working_paper(wp.id, approver_id="Manager")
    wp_svc.lock_working_paper(wp.id, locker_id="Partner Lead")

    # Reopen as Partner
    reopened_wp = wp_svc.reopen_working_paper(
        ReopenWorkingPaperDTO(
            working_paper_id=wp.id,
            reopened_by="Partner Lead",
            reason="Additional GST notice received for Q3.",
        )
    )
    assert reopened_wp.status == WorkingPaperStatusEnum.REOPENED
    assert reopened_wp.version == 2
    assert not reopened_wp.is_locked

    # Check version snapshot reconstruction
    snapshots = wp_svc.list_historical_versions(wp.id)
    assert len(snapshots) == 1
    snap_v1 = snapshots[0]
    assert snap_v1.version == 1
    assert snap_v1.title == "Statutory Tax Dues v1"
    assert "V1 conclusion" in snap_v1.conclusion
    assert len(snap_v1.sections) == 1
    assert snap_v1.sections[0]["title"] == "Work Done v1"

    # Direct query of specific snapshot
    v1_reconstructed = wp_svc.get_version_snapshot(wp.id, 1)
    assert v1_reconstructed is not None
    assert v1_reconstructed.version == 1
    assert v1_reconstructed.conclusion == "V1 conclusion: No major tax liabilities observed."


def test_working_paper_canonical_audit_graph_integration_and_workbench_dto(workbench_env) -> None:
    """Verify Working Paper represents Objective, Risk, Assertion, Procedure, Population, Sampling, Testing, Evidence, Exceptions, Findings, Conclusion, Reviewer, Sign-off, Version."""
    eng, wp_svc, matrix_svc, db_manager = workbench_env

    # 1. Create Risk
    with db_manager.session_scope() as session:
        m_repo = AuditMatrixRepository(session)
        risk = m_repo.add_risk(
            AuditRisk(
                engagement_id=eng.id,
                risk_code="RSK-REV-01",
                title="Revenue Overstatement Risk",
                category="Revenue",
                description="Risk of premature revenue recognition before delivery.",
                financial_statement_area="Revenue",
                assertions=[AssertionEnum.OCCURRENCE, AssertionEnum.CUT_OFF],
                inherent_risk=RiskSeverityEnum.HIGH,
                control_risk=RiskSeverityEnum.MEDIUM,
                derived_romm=RiskSeverityEnum.HIGH,
            )
        )

        # 2. Create Procedure
        proc = m_repo.add_procedure(
            AuditProcedure(
                engagement_id=eng.id,
                procedure_code="PRC-REV-CUTOFF",
                objective="Vouch dispatch notes and e-way bills 15 days around balance sheet date.",
                account_area="Revenue",
                population_definition="Invoices issued between March 15 and April 15.",
                linked_risk_ids=[risk.id],
                assertions=[AssertionEnum.CUT_OFF, AssertionEnum.OCCURRENCE],
            )
        )

        # 3. Create Core Audit Engine Samples & Exceptions
        c_repo = CoreAuditEngineRepository(session)
        c_repo.add_sample_item(
            AuditSampleItemTest(
                procedure_id=proc.id,
                item_identifier="INV-2025-0891",
                account_code="4001",
                expected_value_paise=50000000,
                actual_value_paise=50000000,
                difference_paise=0,
                tested_by="Lead Auditor",
            )
        )
        c_repo.add_exception(
            AuditException(
                engagement_id=eng.id,
                procedure_id=proc.id,
                exception_code="EXC-REV-01",
                title="Dispatch note dated next financial year",
                source="Cut-Off Vouching",
                rule="SA 330 Timing",
                severity="High",
                amount_paise=12000000,
            )
        )

        # 4. Create Finding
        finding = m_repo.add_finding(
            AuditFinding(
                engagement_id=eng.id,
                procedure_id=proc.id,
                risk_id=risk.id,
                title="Early Revenue Recognition Finding",
                description="Revenue recognized in current year without proof of delivery.",
                amount_paise=12000000,
            )
        )

        # 5. Create Evidence
        evidence = m_repo.add_evidence(
            AuditEvidence(
                engagement_id=eng.id,
                procedure_id=proc.id,
                title="E-Way Bill EWB-99182",
                excerpt_or_reference="E-Way Bill generated 2026-04-02",
                source="GST Portal Extract",
                content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )
        )

    # 6. Create Working Paper linking to this Procedure
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-001",
            title="Revenue Cut-Off Working Paper",
            area="Revenue",
            preparer_id="Lead Auditor",
            procedure_ids=[proc.id],
        )
    )

    # 7. Query Workbench Data
    wb = wp_svc.get_workbench_data(wp.id)

    # Verify all canonical representations are populated
    assert wb.working_paper.id == wp.id
    assert wb.version == 1
    assert "Vouch dispatch notes" in wb.objective
    assert len(wb.risks) >= 1
    assert wb.risks[0].risk_code == "RSK-REV-01"
    assert "Cut-Off" in wb.assertions or AssertionEnum.CUT_OFF.value in wb.assertions
    assert len(wb.procedures) >= 1
    assert wb.procedures[0].procedure_code == "PRC-REV-CUTOFF"
    assert "March 15 and April 15" in wb.population
    assert len(wb.samples) >= 1
    assert wb.samples[0]["item_identifier"] == "INV-2025-0891"
    assert len(wb.exceptions) >= 1
    assert wb.exceptions[0]["exception_code"] == "EXC-REV-01"
    assert len(wb.findings) >= 1
    assert wb.findings[0].title == "Early Revenue Recognition Finding"
    assert len(wb.evidence_items) >= 1
    assert wb.evidence_items[0].title == "E-Way Bill EWB-99182"
