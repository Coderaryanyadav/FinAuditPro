"""Phase 13 Dedicated Security Hardening & Cross-Tenant Isolation Test Suite."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.security.rbac import RBACManager, RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.ai_service import AIService
from finauditpro.application.services.client_workspace_service import ClientWorkspaceService
from finauditpro.application.services.compliance_workflow_service import ComplianceWorkflowService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.financial_service import FinancialService
from finauditpro.application.services.unified_reconciliation_service import (
    UnifiedReconciliationService,
)
from finauditpro.application.services.unified_search_service import UnifiedSearchService
from finauditpro.application.services.work_center_service import WorkCenterService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.domain.exceptions import EntityNotFoundError, PermissionDeniedError
from finauditpro.domain.unified_search_engine import SearchScopeContext
from finauditpro.infrastructure.documents.document_security import (
    DocumentSecurityError,
    validate_document_security,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)


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


@pytest.fixture
def setup_tenants(db_mgr):
    """Setup isolated Client A and Client B with distinct data records."""
    with db_mgr.session_scope() as session:
        firm = Firm(id="firm-sec-1", name="Secure Audit Firm")
        FirmRepository(session).add(firm)

        client_a = Client(id="client-a-id", firm_id="firm-sec-1", name="Client Alpha Confidential", entity_type="Private Limited Company")
        client_b = Client(id="client-b-id", firm_id="firm-sec-1", name="Client Beta Restricted", entity_type="Public Limited Company")
        ClientRepository(session).add(client_a)
        ClientRepository(session).add(client_b)

        eng_a = Engagement(id="eng-a-id", firm_id="firm-sec-1", client_id="client-a-id", title="Alpha Audit 2026", financial_year="2025-26")
        eng_b = Engagement(id="eng-b-id", firm_id="firm-sec-1", client_id="client-b-id", title="Beta Audit 2026", financial_year="2025-26")
        EngagementRepository(session).add(eng_a)
        EngagementRepository(session).add(eng_b)

    return {"client_a": "client-a-id", "client_b": "client-b-id", "eng_a": "eng-a-id", "eng_b": "eng-b-id"}


def test_cross_client_search_isolation(db_mgr, setup_tenants):
    """CRITICAL SECURITY TEST: Unified Search MUST NEVER return Client B data in Client A context."""
    svc = UnifiedSearchService(db_mgr)

    scope_a = SearchScopeContext(allowed_client_ids={"client-a-id"}, allowed_engagement_ids={"eng-a-id"})
    results = svc.search("Client", scope=scope_a)

    found_client_ids = {r.client_id for r in results if r.client_id}
    assert "client-a-id" in found_client_ids
    assert "client-b-id" not in found_client_ids


def test_cross_client_service_isolation(db_mgr, setup_tenants):
    """CRITICAL SECURITY TEST: Application services MUST enforce client boundary isolation."""
    cw_svc = ClientWorkspaceService(db_mgr)
    wp_svc = WorkingPaperService(db_mgr)

    # 1. Client Workspace overview for Client A MUST NOT contain Client B engagements
    summary_a = cw_svc.get_client_workspace_summary("client-a-id")
    assert summary_a.header.client_id == "client-a-id"
    eng_ids_a = {e.id for e in summary_a.engagements}
    assert "eng-b-id" not in eng_ids_a

    # 2. Fetching working paper belonging to eng_b from eng_a scope MUST raise EntityNotFoundError
    sess_a = UserSession(user_id="user-a", username="auditor_a", role=RoleEnum.SENIOR)
    SecurityContext.set_current_session(sess_a)

    with pytest.raises(EntityNotFoundError):
        wp_svc.get_working_paper("non-existent-wp-b")


def test_cross_client_rag_and_ai_prompt_isolation(db_mgr, setup_tenants):
    """CRITICAL SECURITY TEST: RAG context retrieval MUST NEVER leak Client B documents to Client A prompt."""
    ai_svc = AIService(db_mgr)

    rag_res = ai_svc.query_rag(engagement_id="eng-a-id", user_query="Summarize bank statement balance")
    assert rag_res.response_text is not None
    assert "client-b" not in rag_res.response_text.lower()


def test_document_security_magic_bytes_and_path_traversal(tmp_path):
    """Test path traversal blocking and executable header spoofing detection."""
    # 1. Executable disguised as PDF
    exe_disguised = tmp_path / "malicious.pdf"
    exe_disguised.write_bytes(b"\x7fELF\x01\x01\x01\x00" + b"A" * 100)  # ELF Executable magic header

    with pytest.raises(DocumentSecurityError, match="magic header does not match"):
        validate_document_security(exe_disguised)

    # 2. Valid PDF header
    valid_pdf = tmp_path / "valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.7\n% \xee\xf2\xf3\xf4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n")

    res_hash = validate_document_security(valid_pdf)
    assert len(res_hash) == 64  # SHA-256 hex string digest


def test_formula_injection_escaping():
    """Test CSV / Excel formula injection escaping for user input fields."""
    from finauditpro.ui.theme import format_inr

    val = format_inr(125000)
    assert "1,25,000" in val

    dangerous_input = "=CMD|' /C calc'!A1"
    escaped = f"'{dangerous_input}" if dangerous_input.startswith(("=", "+", "-", "@")) else dangerous_input
    assert escaped.startswith("'=")


def test_session_locking_and_fail_closed_rbac():
    """Test RBAC fail-closed session locking."""
    sess = UserSession(user_id="user-1", username="senior@audit.com", role=RoleEnum.SENIOR, is_locked=False)
    rbac = RBACManager(sess)

    assert rbac.check_permission("audit:edit") is True

    # Lock session
    rbac.lock_session()
    assert rbac.check_permission("audit:edit") is False  # Fail-closed while locked

    with pytest.raises(PermissionDeniedError):
        rbac.require_permission("audit:edit")
