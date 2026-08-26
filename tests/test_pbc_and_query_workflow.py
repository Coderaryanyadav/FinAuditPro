"""Integration tests for PBC Document Request and Audit Query lifecycle."""

from pathlib import Path

import pytest

from finauditpro.application.services.audit_query_service import AuditQueryService
from finauditpro.application.services.document_request_service import DocumentRequestService
from finauditpro.domain.audit_matrix_entities import RiskSeverityEnum
from finauditpro.domain.pbc_and_query_entities import (
    AuditQueryStatusEnum,
    DocumentRequestStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def db_mgr(tmp_path: Path) -> DatabaseManager:
    from finauditpro.infrastructure.persistence.models import (
        ClientModel,
        EngagementModel,
        FirmModel,
    )
    db = DatabaseManager(db_path=tmp_path / "test_pbc_query.db")
    db.create_tables()
    with db.session_scope() as session:
        firm = FirmModel(id="firm-01", name="Test CA Firm")
        session.add(firm)
        client = ClientModel(id="client-01", firm_id="firm-01", name="Test Client Corp")
        session.add(client)
        eng1 = EngagementModel(id="test-eng-pbc-01", firm_id="firm-01", client_id="client-01", financial_year="2025-26")
        eng2 = EngagementModel(id="test-eng-query-01", firm_id="firm-01", client_id="client-01", financial_year="2025-26")
        session.add_all([eng1, eng2])
    return db


def test_pbc_request_lifecycle(db_mgr: DatabaseManager) -> None:
    service = DocumentRequestService(db_mgr)
    eng_id = "test-eng-pbc-01"

    # 1. Seed statutory package
    seeded = service.seed_default_pbc_package(eng_id)
    assert len(seeded) >= 7
    assert seeded[0].status == DocumentRequestStatusEnum.REQUESTED

    # 2. Create custom request
    req = service.create_request(
        engagement_id=eng_id,
        title="Custom Board Resolutions",
        description="Extract of board resolutions approving borrowing limits under Sec 180(1)(c)",
        period="FY 2025-26",
        contact_name="Company Secretary",
        due_date="2026-09-15",
    )
    assert req.id is not None
    assert req.title == "Custom Board Resolutions"

    # 3. Status transitions
    updated = service.update_status(req.id, DocumentRequestStatusEnum.UNDER_REVIEW, reviewer_notes="Received via portal")
    assert updated.status == DocumentRequestStatusEnum.UNDER_REVIEW
    assert updated.reviewer_notes == "Received via portal"

    # 4. Attach document
    attached = service.attach_document(req.id, "doc-uuid-12345")
    assert "doc-uuid-12345" in attached.uploaded_doc_ids

    # 5. List requests
    all_reqs = service.list_requests(eng_id)
    assert len(all_reqs) >= 8


def test_audit_query_and_escalation_workflow(db_mgr: DatabaseManager) -> None:
    query_service = AuditQueryService(db_mgr)
    eng_id = "test-eng-query-01"

    # 1. Raise query
    query = query_service.raise_query(
        engagement_id=eng_id,
        audit_area="Trade Receivables",
        query_text="Provide debtor balance confirmation for M/s Apex Enterprises exceeding 180 days (₹14,50,000).",
        assigned_to="Senior Auditor",
        client_contact="Accounts Lead",
        due_date="2026-09-20",
    )
    assert query.id is not None
    assert query.status == AuditQueryStatusEnum.SENT_TO_CLIENT

    # 2. Record client response
    responded = query_service.record_client_response(
        query_id=query.id,
        response_text="Customer has disputed invoice #992 due to product quality defect.",
    )
    assert responded.status == AuditQueryStatusEnum.CLIENT_RESPONDED
    assert responded.response_text is not None

    # 3. Escalate to Audit Finding
    escalated_query, finding = query_service.escalate_to_finding(
        query_id=query.id,
        finding_title="Disputed Debtor Balance Unprovided",
        finding_description="M/s Apex Enterprises balance of ₹14.5L disputed due to defect; no ECL/provision created.",
        severity=RiskSeverityEnum.HIGH,
        amount_paise=145000000,
    )
    assert escalated_query.status == AuditQueryStatusEnum.ESCALATED_TO_FINDING
    assert escalated_query.escalated_finding_id == finding.id
    assert finding.amount_paise == 145000000
    assert finding.title == "Disputed Debtor Balance Unprovided"
