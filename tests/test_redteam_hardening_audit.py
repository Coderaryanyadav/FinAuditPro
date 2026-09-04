"""Hostile red-team adversarial tests proving resolution of P0/P1 security, accounting, and finalization findings."""

from datetime import datetime, timezone
import pytest

from finauditpro.application.audit_adjustment_dtos import CreateAJEDTO, CreateAJELineDTO
from finauditpro.application.completion_dtos import PartnerSignoffDTO
from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.security.rbac import RBACManager, RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.application.services.engagement_finalization_service import EngagementFinalizationService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.working_paper_service import CreateWorkingPaperDTO, WorkingPaperService
from finauditpro.domain.audit_adjustment_entities import AuditJournalEntry, AuditJournalLine
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
)
from finauditpro.domain.exceptions import PermissionDeniedError, ValidationError
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)


def test_redteam_session_unlock_bypass_blocked() -> None:
    """FIND-SEC-001: Verifies that unlock_session rejects None passcode and SecurityContext blocks locked sessions."""
    session = UserSession(user_id="auditor-1", username="auditor_rajesh", role=RoleEnum.PARTNER)
    rbac = RBACManager(session)

    # Lock session
    rbac.lock_session()
    assert session.is_locked is True

    # Attack 1: Attempt to unlock with None / empty passcode
    with pytest.raises(ValueError, match="Passcode is required to unlock session"):
        rbac.unlock_session(None)
    assert session.is_locked is True

    with pytest.raises(ValueError, match="Passcode is required to unlock session"):
        rbac.unlock_session("")
    assert session.is_locked is True

    # Attack 2: SecurityContext.enforce_permission must fail-closed on locked session
    SecurityContext.set_current_session(session)
    with pytest.raises(PermissionDeniedError, match="Workstation is locked"):
        SecurityContext.enforce_permission("firm:create", [RoleEnum.PARTNER])

    SecurityContext.clear()


def test_redteam_double_entry_line_level_invariants() -> None:
    """FIND-ACC-001: Verifies that AJE rejects concurrent Dr/Cr amounts on a line or zero-amount lines."""
    # Attack 1: Line with concurrent Dr and Cr amounts (Dr ₹100, Cr ₹100 on same line)
    entry_concurrent = AuditJournalEntry(
        engagement_id="ENG-1",
        aje_number="AJE-BAD-1",
        entry_date="2025-03-31",
        title="Invalid concurrent Dr Cr",
        narration="Bad entry",
        reason="Testing",
        prepared_by="auditor",
        lines=[
            AuditJournalLine(
                entry_id="AJE-BAD-1",
                line_no=1,
                account_code="1001",
                account_name="Cash",
                debit_paise=10000,
                credit_paise=10000,  # Invalid: both Dr and Cr on same line
            ),
            AuditJournalLine(
                entry_id="AJE-BAD-1",
                line_no=2,
                account_code="2001",
                account_name="Payable",
                debit_paise=10000,
                credit_paise=10000,
            ),
        ],
    )
    with pytest.raises(ValidationError, match="cannot have both debit"):
        entry_concurrent.validate_double_entry()

    # Attack 2: Line with zero Dr and zero Cr
    entry_zero = AuditJournalEntry(
        engagement_id="ENG-1",
        aje_number="AJE-BAD-2",
        entry_date="2025-03-31",
        title="Invalid zero line",
        narration="Bad entry",
        reason="Testing",
        prepared_by="auditor",
        lines=[
            AuditJournalLine(
                entry_id="AJE-BAD-2",
                line_no=1,
                account_code="1001",
                account_name="Cash",
                debit_paise=10000,
                credit_paise=0,
            ),
            AuditJournalLine(
                entry_id="AJE-BAD-2",
                line_no=2,
                account_code="2001",
                account_name="Payable",
                debit_paise=0,
                credit_paise=10000,
            ),
            AuditJournalLine(
                entry_id="AJE-BAD-2",
                line_no=3,
                account_code="3001",
                account_name="Ghost Zero Account",
                debit_paise=0,
                credit_paise=0,  # Invalid zero line
            ),
        ],
    )
    with pytest.raises(ValidationError, match="must have a non-zero debit or credit amount"):
        entry_zero.validate_double_entry()


def test_redteam_finalization_mutation_bypass_blocked(tmp_path) -> None:
    """FIND-FIN-001: Verifies that finalized/locked engagements strictly reject post-finalization mutations."""
    db_file = tmp_path / "finalization_bypass_test.db"
    db_manager = initialize_database(db_file)

    # 1. Setup completed/locked engagement
    with db_manager.session_scope() as session:
        firm = Firm(id="firm-redteam", name="RedTeam Audit Firm")
        FirmRepository(session).add(firm)
        client = Client(id="client-redteam", firm_id=firm.id, name="RedTeam Target Client")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-LOCKED-001",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.COMPLETED,  # Finalized and locked!
        )
        EngagementRepository(session).add(eng)

    # Attack 1: Attempt to create AJE on locked engagement
    adj_service = AuditAdjustmentService(db_manager)
    with pytest.raises(ValidationError, match="Tamper-Seal Invariant"):
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id="ENG-LOCKED-001",
                aje_number="AJE-HACK-01",
                entry_date="2025-03-31",
                title="Illicit post-lock adjustment",
                narration="Trying to mutate finalized books",
                reason="Redteam bypass attempt",
                lines=[
                    CreateAJELineDTO(account_code="1001", account_name="Cash", debit_paise=50000, credit_paise=0),
                    CreateAJELineDTO(account_code="2001", account_name="Payable", debit_paise=0, credit_paise=50000),
                ],
            )
        )

    # Attack 2: Attempt to import financial dataset on locked engagement
    dummy_csv = tmp_path / "tb_attack.csv"
    dummy_csv.write_text("Account,Debit,Credit\n1001,100,0\n2001,0,100\n")
    fin_service = FinancialDataService(db_manager)
    with pytest.raises(ValidationError, match="Tamper-Seal Invariant"):
        fin_service.import_financial_dataset(
            ImportDatasetDTO(
                engagement_id="ENG-LOCKED-001",
                dataset_name="Attack Dataset",
                file_path=str(dummy_csv),
            )
        )

    # Attack 3: Attempt to upload document on locked engagement
    doc_service = DocumentService(db_manager)
    dummy_doc = tmp_path / "fake_invoice.txt"
    dummy_doc.write_text("Fake invoice details")
    with pytest.raises(ValidationError, match="Tamper-Seal Invariant"):
        doc_service.upload_and_process_document(
            UploadDocumentDTO(engagement_id="ENG-LOCKED-001", file_path=str(dummy_doc))
        )

    # Attack 4: Attempt to create working paper on locked engagement
    wp_service = WorkingPaperService(db_manager)
    with pytest.raises(ValidationError, match="Tamper-Seal Invariant"):
        wp_service.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id="ENG-LOCKED-001",
                index_reference="WP-HACK",
                title="Post-lock working paper",
                area="General",
                preparer_id="attacker",
            )
        )
