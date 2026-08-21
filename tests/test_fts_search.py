"""Integration tests for FTS5 document full-text search and strict cross-engagement retrieval isolation."""

import pytest

from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.domain.document_entities import DocumentCategoryEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_search_services(tmp_path):
    db_file = tmp_path / "test_fts.db"
    manager = DatabaseManager(db_path=db_file)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)
    doc_svc = DocumentService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="FTS Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="FTS Client"))

    eng_a = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )
    eng_b = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2024-25")
    )

    return manager, eng_a, eng_b, doc_svc


def test_fts5_cross_engagement_search_isolation(setup_search_services, tmp_path) -> None:
    """PROVE that FTS5 search in Engagement A returns ZERO documents from Engagement B."""
    _manager, eng_a, eng_b, doc_svc = setup_search_services

    # Create document file for Engagement A
    doc_a_file = tmp_path / "tax_eng_a.txt"
    doc_a_file.write_text(
        "Tax Return FY 2025-26. Section 80C Deduction: INR 1,50,000 for Engagement A.",
        encoding="utf-8",
    )

    # Create document file for Engagement B
    doc_b_file = tmp_path / "tax_eng_b.txt"
    doc_b_file.write_text(
        "Tax Return FY 2024-25. Section 80C Deduction: INR 1,50,000 for Engagement B.",
        encoding="utf-8",
    )

    # Upload Document A to Engagement A
    doc_a = doc_svc.upload_and_process_document(
        UploadDocumentDTO(
            engagement_id=eng_a.id,
            file_path=str(doc_a_file),
            category=DocumentCategoryEnum.TAX_RETURN,
        )
    )

    # Upload Document B to Engagement B
    doc_b = doc_svc.upload_and_process_document(
        UploadDocumentDTO(
            engagement_id=eng_b.id,
            file_path=str(doc_b_file),
            category=DocumentCategoryEnum.TAX_RETURN,
        )
    )

    # Search inside Engagement A for "Section 80C"
    results_a = doc_svc.search_documents(eng_a.id, "Section 80C")
    assert len(results_a) == 1
    assert results_a[0].document_id == doc_a.id
    assert "Engagement A" in results_a[0].snippet
    assert "Engagement B" not in results_a[0].snippet  # Zero leakage!

    # Search inside Engagement B for "Section 80C"
    results_b = doc_svc.search_documents(eng_b.id, "Section 80C")
    assert len(results_b) == 1
    assert results_b[0].document_id == doc_b.id
    assert "Engagement B" in results_b[0].snippet


def test_fts5_soft_delete_desync(setup_search_services, tmp_path) -> None:
    """Verify that soft-deleting a document desyncs FTS5 while preserving audit provenance."""
    _manager, eng_a, _eng_b, doc_svc = setup_search_services

    doc_file = tmp_path / "audit_memo.txt"
    doc_file.write_text("Confidential Statutory Audit Report Memorandum", encoding="utf-8")

    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(
            engagement_id=eng_a.id,
            file_path=str(doc_file),
            category=DocumentCategoryEnum.AUDIT_REPORT,
        )
    )

    # Search before deletion
    hits = doc_svc.search_documents(eng_a.id, "Memorandum")
    assert len(hits) == 1

    # Soft Delete Document
    doc_svc.delete_document(doc.id)

    # Search after deletion -> 0 results from FTS
    hits_after = doc_svc.search_documents(eng_a.id, "Memorandum")
    assert len(hits_after) == 0
