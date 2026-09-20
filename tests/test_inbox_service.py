"""Unit tests for InboxService and human-in-the-loop classification approval."""

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.dtos_inbox import InboxFilterDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.inbox_service import InboxService
from finauditpro.infrastructure.persistence.database import DatabaseManager


def test_inbox_service_empty_db(tmp_path) -> None:
    """Test InboxService returns zero items and empty summary on fresh DB."""
    db_path = tmp_path / "test_inbox_empty.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    service = InboxService(db_manager)
    summary = service.get_inbox_items(InboxFilterDTO())

    assert summary.total_items == 0
    assert summary.needs_review_count == 0
    assert len(summary.items) == 0


def test_inbox_service_document_intake_and_human_approval(tmp_path) -> None:
    """Test uploaded document aggregation, AI confidence scoring, and human acceptance/override."""
    db_path = tmp_path / "test_inbox_approval.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    doc_svc = DocumentService(db_manager)
    inbox_svc = InboxService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Inbox CA Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Inbox Client Pvt Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    # Create dummy PDF file for ingestion
    sample_file = tmp_path / "March_Bank_Statement.pdf"
    sample_file.write_bytes(b"%PDF-1.5 %EOF\nDummy Bank Statement Content")

    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng.id, file_path=str(sample_file))
    )
    assert doc.id is not None

    # Fetch inbox summary
    summary = inbox_svc.get_inbox_items(InboxFilterDTO(tab="ALL"))
    assert summary.total_items >= 1

    item = next(i for i in summary.items if i.id == doc.id)
    assert item.title == "March_Bank_Statement.pdf"
    assert item.client_name == "Inbox Client Pvt Ltd"

    # Test human approval / category override
    success = inbox_svc.accept_classification(doc.id, human_category="Bank Statement")
    assert success is True

    # Re-fetch inbox summary to verify state change to ACCEPTED
    updated_summary = inbox_svc.get_inbox_items(InboxFilterDTO(tab="ALL"))
    updated_item = next(i for i in updated_summary.items if i.id == doc.id)
    assert updated_item.status == "ACCEPTED"
    assert updated_item.human_approval_state in ("APPROVED", "OVERRIDDEN")
    assert updated_item.detected_category == "Bank Statement"


def test_inbox_service_document_rejection(tmp_path) -> None:
    """Test human rejection of incoming evidence document."""
    db_path = tmp_path / "test_inbox_reject.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    doc_svc = DocumentService(db_manager)
    inbox_svc = InboxService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Reject Test Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Reject Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    sample_file = tmp_path / "Corrupted_File.pdf"
    sample_file.write_bytes(b"%PDF-1.4 Corrupted")

    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng.id, file_path=str(sample_file))
    )

    reject_ok = inbox_svc.reject_item(doc.id, reason="Corrupted PDF bytes")
    assert reject_ok is True

    summary = inbox_svc.get_inbox_items(InboxFilterDTO(tab="ALL"))
    item = next(i for i in summary.items if i.id == doc.id)
    assert item.status == "REJECTED"
    assert item.human_approval_state == "REJECTED"
