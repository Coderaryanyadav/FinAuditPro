"""Integration tests for DocumentService workflows and full-text search."""

import pytest

from finauditpro.application.document_dtos import UploadDocumentDTO
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.document_entities import DocumentCategoryEnum, DocumentStatusEnum
from finauditpro.infrastructure.documents.document_pipeline import DocumentPipeline
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_services(tmp_path):
    db_path = tmp_path / "test_doc_svc.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Doc Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Doc Client Pvt Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    doc_pipeline = DocumentPipeline(storage_dir=tmp_path / "storage")
    doc_svc = DocumentService(manager, pipeline=doc_pipeline)

    return manager, eng, doc_svc


def test_upload_process_and_search_document(setup_services, tmp_path) -> None:
    _manager, eng, doc_svc = setup_services

    sample_doc = tmp_path / "tax_computation.txt"
    sample_doc.write_text(
        "Income Tax Computation FY 2025-26\nGross Total Income: INR 50,00,000\nSection 80C Deduction: INR 1,50,000\nNet Tax Payable: INR 12,50,000",
        encoding="utf-8",
    )

    upload_dto = UploadDocumentDTO(
        engagement_id=eng.id,
        file_path=str(sample_doc),
        category=DocumentCategoryEnum.TAX_RETURN,
    )

    doc = doc_svc.upload_and_process_document(upload_dto)
    assert doc.id is not None
    assert doc.status in (DocumentStatusEnum.READY, DocumentStatusEnum.COMPLETED)
    assert doc.page_count == 1

    # Retrieve Details
    details = doc_svc.get_document_details(doc.id)
    assert details.document.filename == "tax_computation.txt"
    assert len(details.pages) == 1

    # Full-Text Search
    search_results = doc_svc.search_documents(eng.id, "Section 80C")
    assert len(search_results) == 1
    assert search_results[0].document_id == doc.id
    assert "Section 80C" in search_results[0].snippet

    # List documents
    doc_list = doc_svc.list_documents_for_engagement(eng.id)
    assert len(doc_list) == 1
