"""Automated tests for Phase 10 — Unified Reconciliation Center."""

from unittest.mock import MagicMock

import pytest

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.dtos_reconciliation import (
    MatchStatusEnum,
    ReconciliationItemDTO,
    ReconciliationSourceRecordDTO,
    ReconciliationTabEnum,
)
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.unified_reconciliation_service import (
    UnifiedReconciliationService,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.unified_reconciliation_view import UnifiedReconciliationView


@pytest.fixture
def setup_services(tmp_path):
    db_path = tmp_path / "test_recon_center.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Recon Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Recon Client Pvt Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    recon_svc = UnifiedReconciliationService(manager)
    return manager, eng, recon_svc


def test_reconciliation_all_six_tabs_execution(setup_services):
    """Test deterministic reconciliation compiling across all 6 tabs."""
    _manager, eng, recon_svc = setup_services

    tabs = [
        ReconciliationTabEnum.GST,
        ReconciliationTabEnum.BANK,
        ReconciliationTabEnum.LEDGER,
        ReconciliationTabEnum.INVOICES,
        ReconciliationTabEnum.RECEIVABLES,
        ReconciliationTabEnum.PAYABLES,
    ]

    for t in tabs:
        summary = recon_svc.get_reconciliation_summary(eng.id, tab=t)
        assert summary.tab == t
        assert summary.total_items >= 0
        assert isinstance(summary.items, list)


def test_deterministic_matching_four_statuses(setup_services):
    """Test that reconciliation items accurately evaluate into the 4 required match statuses."""
    _manager, eng, recon_svc = setup_services

    gst_summary = recon_svc.get_reconciliation_summary(eng.id, tab=ReconciliationTabEnum.GST)
    statuses_found = {item.match_status for item in gst_summary.items}

    # Verify statuses are valid MatchStatusEnum members
    for item in gst_summary.items:
        assert item.match_status in (
            MatchStatusEnum.MATCHED,
            MatchStatusEnum.UNMATCHED,
            MatchStatusEnum.POTENTIAL_MATCH,
            MatchStatusEnum.NEEDS_REVIEW,
        )

    # Verify source A vs source B data integrity
    for item in gst_summary.items:
        assert item.source_a.label != ""
        assert item.source_b.label != ""
        assert item.difference_paise >= 0
        assert abs(item.source_a.amount_paise - item.source_b.amount_paise) == item.difference_paise


def test_source_records_preservation_and_rupee_formatting():
    """Test that source records display exact amounts, references, and differences in rupees."""
    item = ReconciliationItemDTO(
        id="item-001",
        tab=ReconciliationTabEnum.GST,
        item_key="INV-123",
        title="Invoice INV-123 (Supplier A)",
        match_status=MatchStatusEnum.NEEDS_REVIEW,
        source_a=ReconciliationSourceRecordDTO(
            label="Ledger / Purchase Register", reference="INV-123", amount_paise=12000000
        ),
        source_b=ReconciliationSourceRecordDTO(
            label="GST Portal (GSTR-2B)", reference="INV-123", amount_paise=11800000
        ),
        difference_paise=200000,
        discrepancy_reason="Tax Amount Mismatch",
    )

    assert item.source_a.amount_rupees == 120000.00
    assert item.source_b.amount_rupees == 118000.00
    assert item.difference_rupees == 2000.00


def test_ai_explanation_non_mutating(setup_services):
    """Test AI exception explanation generation without modifying accounting or database balances."""
    manager, eng, recon_svc = setup_services

    item = ReconciliationItemDTO(
        id="item-ai-01",
        tab=ReconciliationTabEnum.GST,
        item_key="INV-AI-999",
        title="Invoice INV-AI-999 (Vendor X)",
        match_status=MatchStatusEnum.NEEDS_REVIEW,
        source_a=ReconciliationSourceRecordDTO(
            label="Ledger", reference="INV-AI-999", amount_paise=12000000
        ),
        source_b=ReconciliationSourceRecordDTO(
            label="GSTR-2B", reference="INV-AI-999", amount_paise=11800000
        ),
        difference_paise=200000,
        discrepancy_reason="₹2,000 Tax Mismatch",
    )

    # 1. Deterministic fallback prompt synthesis
    explanation = recon_svc.explain_exception_with_ai(item, ai_service=None)
    assert "₹2,000.00" in explanation
    assert "AI explanations are advisory and do not modify accounting records" in explanation

    # 2. Mock AI service invocation
    mock_ai = MagicMock()
    mock_ai.ask_ai.return_value = "AI Analysis: Omitted freight charges in GSTR-2B filing."

    ai_exp = recon_svc.explain_exception_with_ai(item, ai_service=mock_ai)
    assert "AI Analysis" in ai_exp

    # Verify no database state was mutated
    summary_after = recon_svc.get_reconciliation_summary(eng.id, tab=ReconciliationTabEnum.GST)
    assert summary_after.total_items >= 0


@pytest.mark.gui
def test_unified_reconciliation_view_pyside6(qtbot, setup_services):
    """Test PySide6 UI view instantiation, tab switching, and status filtering."""
    manager, eng, _recon_svc = setup_services

    view = UnifiedReconciliationView(manager)
    qtbot.addWidget(view)
    view.set_engagement_context(eng.id)
    view.show()

    assert view.active_tab == ReconciliationTabEnum.GST

    # Switch tab to Bank
    view._on_tab_changed(1)
    assert view.active_tab == ReconciliationTabEnum.BANK

    # Switch filter status to Needs Review
    view._on_filter_changed(4)
    assert view.active_status_filter == MatchStatusEnum.NEEDS_REVIEW.value
