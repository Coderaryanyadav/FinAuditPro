"""Tests for Phase 11 Compliance Workflow engine, service, and PySide6 UI view."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.services.compliance_workflow_service import ComplianceWorkflowService
from finauditpro.domain.compliance_workflow_engine import (
    ComplianceItemDTO,
    ComplianceItemStatusEnum,
    ComplianceWorkflowEngine,
)
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.domain.exceptions import ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)
from finauditpro.ui.views.compliance_view import ComplianceView


@pytest.fixture
def app():
    app_inst = QApplication.instance()
    if not app_inst:
        app_inst = QApplication(sys.argv)
    return app_inst


@pytest.fixture
def db_mgr():
    db = DatabaseManager(":memory:")
    db.create_tables()
    return db


def test_deterministic_applicability_rules():
    """Test deterministic rule derivation for CARO, Tax Audit, CSR, and ROC returns."""
    # 1. Small private company (Turnover <= 10 Cr, Borrowings <= 1 Cr)
    items_small = ComplianceWorkflowEngine.determine_compliance_items(
        engagement_id="eng-1",
        client_name="Small Tech Pvt Ltd",
        entity_type="PRIVATE_LIMITED",
        turnover_rupees=50000000.0,
        borrowings_rupees=5000000.0,
        net_profit_rupees=2000000.0,
    )
    caro_small = next(i for i in items_small if i.rule_code == "CARO_2020")
    assert caro_small.applicable is False
    assert caro_small.status == ComplianceItemStatusEnum.NOT_APPLICABLE
    assert "Exempt" in caro_small.applicability_reason

    csr_small = next(i for i in items_small if i.rule_code == "SEC_135_CSR")
    assert csr_small.applicable is False
    assert csr_small.status == ComplianceItemStatusEnum.NOT_APPLICABLE

    # 2. Large company exceeding CARO & CSR thresholds
    items_large = ComplianceWorkflowEngine.determine_compliance_items(
        engagement_id="eng-2",
        client_name="Large Enterprise Ltd",
        entity_type="PUBLIC_LIMITED",
        turnover_rupees=150000000.0,
        borrowings_rupees=20000000.0,
        net_profit_rupees=60000000.0,
    )
    caro_large = next(i for i in items_large if i.rule_code == "CARO_2020")
    assert caro_large.applicable is True
    assert caro_large.due_date == "2026-09-30"

    csr_large = next(i for i in items_large if i.rule_code == "SEC_135_CSR")
    assert csr_large.applicable is True
    assert csr_large.due_date == "2026-03-31"


def test_status_transition_invariants():
    """Test valid and invalid workflow status transitions."""
    # Valid transition
    assert ComplianceWorkflowEngine.validate_status_transition(
        ComplianceItemStatusEnum.NOT_STARTED, ComplianceItemStatusEnum.IN_PROGRESS
    ) is True

    assert ComplianceWorkflowEngine.validate_status_transition(
        ComplianceItemStatusEnum.IN_PROGRESS, ComplianceItemStatusEnum.WAITING_FOR_CLIENT
    ) is True

    assert ComplianceWorkflowEngine.validate_status_transition(
        ComplianceItemStatusEnum.READY_FOR_REVIEW, ComplianceItemStatusEnum.COMPLETED
    ) is True

    # Invalid transition (e.g. direct NOT_STARTED to COMPLETED)
    assert ComplianceWorkflowEngine.validate_status_transition(
        ComplianceItemStatusEnum.NOT_STARTED, ComplianceItemStatusEnum.COMPLETED
    ) is False


def test_service_workflow_persistence_and_transitions(db_mgr):
    """Test ComplianceWorkflowService initialization, persistence, and status updates."""
    with db_mgr.session_scope() as session:
        firm = Firm(id="firm-1", name="Alpha Audit Firm")
        FirmRepository(session).add(firm)

        client_repo = ClientRepository(session)
        client = Client(firm_id="firm-1", name="Alpha Corp", entity_type="Private Limited Company")
        client_repo.add(client)

        eng_repo = EngagementRepository(session)
        eng = Engagement(firm_id="firm-1", client_id=client.id, financial_year="2025-26", title="Statutory Audit")
        eng_repo.add(eng)
        eng_id = eng.id

    svc = ComplianceWorkflowService(db_mgr)
    items = svc.initialize_compliance_items(eng_id)
    assert len(items) >= 5

    not_started_item = next(i for i in items if i.status == ComplianceItemStatusEnum.NOT_STARTED)

    # Invalid status update attempt (NOT_STARTED directly to COMPLETED) raises ValidationError
    with pytest.raises(ValidationError):
        svc.update_item_status(
            engagement_id=eng_id,
            item_id=not_started_item.id,
            new_status=ComplianceItemStatusEnum.COMPLETED,
        )

    # Valid status update (NOT_STARTED -> IN_PROGRESS)
    updated = svc.update_item_status(
        engagement_id=eng_id,
        item_id=not_started_item.id,
        new_status=ComplianceItemStatusEnum.IN_PROGRESS,
        notes="Audit fieldwork initiated",
    )
    assert updated.status == ComplianceItemStatusEnum.IN_PROGRESS
    assert updated.notes == "Audit fieldwork initiated"

    # Attach evidence
    ev_item = svc.attach_evidence_to_item(eng_id, not_started_item.id, "DOC-2026-GST.pdf")
    assert "DOC-2026-GST.pdf" in ev_item.evidence


def test_ai_explanation_non_mutating(db_mgr):
    """Test AI compliance explanation generation without modifying statutory due dates or rules."""
    svc = ComplianceWorkflowService(db_mgr)
    dto = ComplianceItemDTO(
        engagement_id="eng-1",
        requirement="ROC Form AOC-4 Filing",
        statutory_head="Companies Act 2013",
        rule_code="ROC_AOC4",
        applicable=True,
        due_date="2026-10-30",
        status=ComplianceItemStatusEnum.IN_PROGRESS,
        evidence=["AOC4_Draft.pdf"],
    )

    meaning_resp = svc.explain_compliance_with_ai(dto, prompt_kind="meaning")
    assert "Statutory Requirement Explanation" in meaning_resp
    assert dto.due_date == "2026-10-30"  # Unaltered

    evidence_resp = svc.explain_compliance_with_ai(dto, prompt_kind="evidence")
    assert "Recommended Audit Evidence" in evidence_resp

    incomplete_resp = svc.explain_compliance_with_ai(dto, prompt_kind="incomplete")
    assert "Incompleteness Rationale" in incomplete_resp


def test_compliance_view_ui(app, db_mgr):
    """Test ComplianceView PySide6 rendering and engagement interaction."""
    view = ComplianceView(db_manager=db_mgr)
    assert view.header.title_lbl.text() == "Statutory Compliance & Workflow Matrix"

    with db_mgr.session_scope() as session:
        firm = Firm(id="firm-1", name="Alpha Audit Firm")
        FirmRepository(session).add(firm)

        client = Client(firm_id="firm-1", name="Beta Industries", entity_type="Public Limited Company")
        ClientRepository(session).add(client)

        eng = Engagement(firm_id="firm-1", client_id=client.id, financial_year="2025-26", title="Statutory Audit")
        EngagementRepository(session).add(eng)

    view.set_active_engagement(eng)
    assert view.wf_table.rowCount() >= 5
    assert view.card_total.value_lbl.text() != "0"
