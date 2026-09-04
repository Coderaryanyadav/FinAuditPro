"""Tests for SA 580 Management Representation Letters (MRL) and SA 560 Subsequent Events."""

from finauditpro.application.audit_completion_dtos import CreateSubsequentEventDTO
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.domain.audit_completion_engine import AuditCompletionEngine
from finauditpro.infrastructure.first_run import initialize_database


def test_sa580_mrl_chronology_validation() -> None:
    # 1. Valid: MRL signed on or before audit report date
    is_valid, msg = AuditCompletionEngine.validate_mrl_chronology(
        mrl_signed_date="2026-08-25", audit_report_date="2026-08-26"
    )
    assert is_valid
    assert "SA 580 Valid" in msg

    # 2. Invalid: MRL signed AFTER audit report date
    is_valid, msg = AuditCompletionEngine.validate_mrl_chronology(
        mrl_signed_date="2026-08-28", audit_report_date="2026-08-26"
    )
    assert not is_valid
    assert "SA 580 Invariant Violation" in msg

    # 3. Invalid: MRL not signed
    is_valid, msg = AuditCompletionEngine.validate_mrl_chronology(
        mrl_signed_date=None, audit_report_date="2026-08-26"
    )
    assert not is_valid
    assert "SA 580 Violation" in msg


def test_sa580_service_mrl_lifecycle(tmp_path: any) -> None:
    db_path = tmp_path / "test_mrl.db"
    db_manager = initialize_database(db_path)

    SecurityContext.set_current_user("auditor-1", RoleEnum.SENIOR_AUDITOR)
    service = AuditCompletionService(db_manager)

    # 1. Generate default MRL
    mrl = service.generate_default_mrl(
        engagement_id="eng-mrl-1",
        financial_year="2025-26",
        requested_date="2026-08-20",
    )
    assert mrl.mrl_number == "MRL-2025-26-001"
    assert len(mrl.clauses) == 6
    assert mrl.status == "Draft Representation Letter"

    # 2. Update to signed
    updated = service.update_mrl_status(
        engagement_id="eng-mrl-1",
        mrl_id=mrl.id,
        status="Signed by Management",
        signed_date="2026-08-24",
        signatory_name="Rajesh Sharma",
        signatory_designation="Managing Director",
        audit_report_date="2026-08-25",
    )
    assert updated.status == "Signed by Management"
    assert updated.signatory_name == "Rajesh Sharma"
    assert updated.is_chronologically_valid


def test_sa560_subsequent_events_log(tmp_path: any) -> None:
    db_path = tmp_path / "test_subseq.db"
    db_manager = initialize_database(db_path)

    SecurityContext.set_current_user("auditor-1", RoleEnum.SENIOR_AUDITOR)
    service = AuditCompletionService(db_manager)

    dto = CreateSubsequentEventDTO(
        event_date="2026-05-15",
        event_type="Adjusting Event (Condition existed at Balance Sheet Date)",
        description="Settlement of customer litigation pending as on 31-Mar-2026 for ₹15 Lakhs",
        estimated_amount_paise=150000000,
        accounting_treatment="Adjusted in Financial Statements (AS 4 / Ind AS 10)",
        is_adjusted_in_fs=True,
        is_disclosed_in_notes=True,
        procedure_applied="Review of subsequent lawyer confirmations and board minutes",
        auditor_conclusion="Verified settlement receipt and AJE #004 posted.",
    )

    saved = service.record_subsequent_event("eng-subseq-1", dto)
    assert saved.is_adjusted_in_fs
    assert saved.estimated_amount_paise == 150000000

    events = service.list_subsequent_events("eng-subseq-1")
    assert len(events) == 1
    assert events[0].description == dto.description
