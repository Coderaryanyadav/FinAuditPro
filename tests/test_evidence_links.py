"""Unit tests for Evidence Linking subsystem."""

import pytest

from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.document_service import (
    CreateEvidenceLinkDTO,
    DocumentService,
    UploadDocumentDTO,
)
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.domain.document_entities import DocumentCategoryEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_evidence_services(tmp_path):
    db_file = tmp_path / "test_evidence.db"
    manager = DatabaseManager(db_path=db_file)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)
    doc_svc = DocumentService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Ev Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Ev Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )
    return manager, eng, doc_svc


def test_create_and_list_evidence_link(setup_evidence_services, tmp_path) -> None:
    _manager, eng, doc_svc = setup_evidence_services

    doc_file = tmp_path / "invoice_101.txt"
    doc_file.write_text("Tax Invoice #INV-101. Gross Amount: INR 5,00,000", encoding="utf-8")

    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(
            engagement_id=eng.id,
            file_path=str(doc_file),
            category=DocumentCategoryEnum.INVOICE,
        )
    )

    link_dto = CreateEvidenceLinkDTO(
        engagement_id=eng.id,
        document_id=doc.id,
        page_number=1,
        target_type="Audit Finding",
        title="Verification of High Value Invoice #INV-101",
        snippet="Gross Amount: INR 5,00,000",
    )

    link = doc_svc.create_evidence_link(link_dto)
    assert link.id is not None
    assert link.page_number == 1
    assert link.title == "Verification of High Value Invoice #INV-101"

    links = doc_svc.list_evidence_links_for_engagement(eng.id)
    assert len(links) == 1
    assert links[0].snippet == "Gross Amount: INR 5,00,000"
