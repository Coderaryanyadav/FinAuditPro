"""Tests for Phase 12 Unified Search engine, FTS5 integration, security isolation, and PySide6 dialog."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.services.unified_search_service import UnifiedSearchService
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.domain.unified_search_engine import (
    SearchResultGroupEnum,
    SearchScopeContext,
    format_search_context,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)
from finauditpro.ui.dialogs.command_palette_dialog import CommandPaletteDialog


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


def test_context_formatting():
    """Test rich search context formatting helper."""
    ctx = format_search_context("ABC Enterprises", "March Bank Statement", "2025-26", "Evidence / Documents")
    assert ctx == "ABC Enterprises | March Bank Statement | FY 2025-26 | Evidence / Documents"


def test_unified_search_across_entities(db_mgr):
    """Test unified searching across Clients, Engagements, and database entities."""
    with db_mgr.session_scope() as session:
        firm = Firm(id="firm-1", name="Apex Audit Firm")
        FirmRepository(session).add(firm)

        client = Client(id="client-1", firm_id="firm-1", name="Apex Manufacturing Pvt Ltd", entity_type="Private Limited Company")
        ClientRepository(session).add(client)

        eng = Engagement(id="eng-1", firm_id="firm-1", client_id="client-1", title="Statutory Audit FY 2025-26", financial_year="2025-26")
        EngagementRepository(session).add(eng)

    svc = UnifiedSearchService(db_mgr)

    # Search for client
    client_results = svc.search("Apex Manufacturing")
    assert len(client_results) >= 1
    c_res = next(r for r in client_results if r.entity_type == "CLIENT")
    assert c_res.group == SearchResultGroupEnum.CLIENTS
    assert "Apex Manufacturing" in c_res.title

    # Search for engagement
    eng_results = svc.search("Statutory Audit")
    assert len(eng_results) >= 1
    e_res = next(r for r in eng_results if r.entity_type == "ENGAGEMENT")
    assert e_res.group == SearchResultGroupEnum.CLIENTS
    assert "Statutory Audit" in e_res.title


def test_security_isolation_client_boundaries(db_mgr):
    """Security Regression Test: Verify search results NEVER cross authorized client boundaries."""
    with db_mgr.session_scope() as session:
        firm = Firm(id="firm-1", name="Secure Audit Firm")
        FirmRepository(session).add(firm)

        # Client A
        cA = Client(id="client-a", firm_id="firm-1", name="Alpha Secret Corp", entity_type="Private Limited Company")
        ClientRepository(session).add(cA)
        engA = Engagement(id="eng-a", firm_id="firm-1", client_id="client-a", title="Alpha Audit 2026", financial_year="2025-26")
        EngagementRepository(session).add(engA)

        # Client B
        cB = Client(id="client-b", firm_id="firm-1", name="Beta Confidential Ltd", entity_type="Public Limited Company")
        ClientRepository(session).add(cB)
        engB = Engagement(id="eng-b", firm_id="firm-1", client_id="client-b", title="Beta Audit 2026", financial_year="2025-26")
        EngagementRepository(session).add(engB)

    svc = UnifiedSearchService(db_mgr)

    # User authorized ONLY for Client A
    scope_A = SearchScopeContext(allowed_client_ids={"client-a"}, allowed_engagement_ids={"eng-a"})
    res_A = svc.search("Audit", scope=scope_A)
    # Must find Alpha Audit, MUST NOT find Beta Audit
    assert any("Alpha" in r.title for r in res_A)
    assert not any("Beta" in r.title for r in res_A)

    # User authorized ONLY for Client B
    scope_B = SearchScopeContext(allowed_client_ids={"client-b"}, allowed_engagement_ids={"eng-b"})
    res_B = svc.search("Audit", scope=scope_B)
    assert any("Beta" in r.title for r in res_B)
    assert not any("Alpha" in r.title for r in res_B)


def test_command_palette_dialog_ui(app, db_mgr):
    """Test CommandPaletteDialog PySide6 rendering and debounced search."""
    dlg = CommandPaletteDialog(db_manager=db_mgr)
    assert dlg.input_field.placeholderText().startswith("Search")

    # Enter search query
    dlg.input_field.setText("Audit")
    dlg._execute_search()
    assert dlg.list_widget.count() >= 1
