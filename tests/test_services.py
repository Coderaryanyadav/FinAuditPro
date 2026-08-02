"""
Comprehensive Service Layer Unit & Integration Test Suite for FinAuditPro.
Verifies business logic, repository interactions, RBAC gates, and document management.
"""

import unittest
import tempfile
import os

from database.database import init_db
from database.repositories.user_repo import UserRepository
from database.repositories.client_repo import ClientRepository
from database.repositories.document_repo import DocumentRepository
from database.repositories.working_paper_repo import WorkingPaperRepository

from services.auth_service import AuthenticationService
from services.client_service import ClientService
from services.document_service import DocumentService
from services.working_paper_service import WorkingPaperService
from core.exceptions import ValidationError, DuplicateRecordError, AuthError, EntityNotFoundError

class TestServices(unittest.TestCase):

    def setUp(self):
        init_db()
        from database.database import engine, SessionLocal
        from database.models import Client, FinancialYear, Engagement
        from sqlalchemy.orm import Session

        # Begin a connection-level transaction so we can roll back after each test
        self._connection = engine.connect()
        self._transaction = self._connection.begin()
        self.session = Session(bind=self._connection)

        # Create dummy client, FY, and engagement to satisfy FK constraints
        self.dummy_client = Client(name="Test Client Corp", gst_number="27AAACB1234F1Z0")
        self.session.add(self.dummy_client)
        self.session.flush()

        from datetime import datetime, timezone
        import uuid
        now_dt = datetime.now(timezone.utc)
        self.dummy_fy = FinancialYear(label=f"2025-{uuid.uuid4().hex[:4]}", start_date=now_dt, end_date=now_dt)
        self.session.add(self.dummy_fy)
        self.session.flush()

        self.dummy_engagement = Engagement(client_id=self.dummy_client.id, financial_year_id=self.dummy_fy.id, audit_type="Statutory", status="Planning")
        self.session.add(self.dummy_engagement)
        self.session.flush()

        from security.security_manager import SecurityManager
        from security.auth import SessionToken
        from security.rbac import UserRole
        self.sm = SecurityManager()
        self.sm.current_session = SessionToken(token_str="test_token", user_id=1, user_email="admin@test.com", role=UserRole.ADMINISTRATOR.value)

        self.user_repo = UserRepository(self.session)
        self.client_repo = ClientRepository(self.session)
        self.doc_repo = DocumentRepository(self.session)
        self.wp_repo = WorkingPaperRepository(self.session)

        self.auth_service = AuthenticationService(self.user_repo)
        self.client_service = ClientService(self.client_repo)
        self.doc_service = DocumentService(self.doc_repo)
        self.wp_service = WorkingPaperService(self.wp_repo)

    def tearDown(self):
        self.sm.current_session = None
        self.session.close()
        # Roll back the outer transaction — leaves the DB pristine for the next test
        self._transaction.rollback()
        self._connection.close()

    def test_client_service_validation(self):
        # Invalid GSTIN format test
        with self.assertRaises(ValidationError):
            self.client_service.create_client(name="Invalid GST Corp", gst_number="INVALID_GSTIN")

        # Invalid PAN format test
        with self.assertRaises(ValidationError):
            self.client_service.create_client(name="Invalid PAN Corp", pan_number="INVALID_PAN")

    def test_document_service_managed_storage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_file = os.path.join(temp_dir, "sample_invoice.pdf")
            with open(sample_file, "wb") as f:
                f.write(b"%PDF-1.4 sample content")

            doc = self.doc_service.upload_document(engagement_id=self.dummy_engagement.id, file_path=sample_file, document_type="Invoice")
            self.assertEqual(doc.file_name, "sample_invoice.pdf")
            self.assertIn(f"data/documents/eng_{self.dummy_engagement.id}", doc.file_path.replace("\\", "/"))
            self.assertTrue(os.path.exists(doc.file_path))

    def test_working_paper_service_index_creation(self):
        index = self.wp_service.create_index(engagement_id=self.dummy_engagement.id, section_code="REV-01", section_name="Revenue Audit")
        self.assertIsNotNone(index.id)
        self.assertEqual(index.section_code, "REV-01")

    # --- RBAC Null-Session Enforcement Tests ---

    def test_rbac_null_session_blocks_create_client(self):
        """Calling create_client without a session must raise AuthError, never silently skip."""
        self.sm.current_session = None  # Revoke session
        with self.assertRaises(AuthError):
            self.client_service.create_client(name="Unauthenticated Corp")

    def test_rbac_null_session_blocks_upload_document(self):
        """Calling upload_document without a session must raise AuthError."""
        self.sm.current_session = None
        with self.assertRaises(AuthError):
            self.doc_service.upload_document(engagement_id=999, file_path="/nonexistent.pdf", document_type="Invoice")

    def test_rbac_null_session_blocks_create_index(self):
        """Calling create_index without a session must raise AuthError."""
        self.sm.current_session = None
        with self.assertRaises(AuthError):
            self.wp_service.create_index(engagement_id=self.dummy_engagement.id, section_code="TEST-01", section_name="Test")

    def test_rbac_null_session_blocks_create_paper(self):
        """Calling create_paper without a session must raise AuthError."""
        self.sm.current_session = None
        with self.assertRaises(AuthError):
            self.wp_service.create_paper(index_id=999, title="Unauthenticated Paper", prepared_by_id=1)

    def test_rbac_null_session_blocks_update_status(self):
        """Calling update_status without a session must raise AuthError."""
        from database.models import WorkingPaper
        self.sm.current_session = None
        dummy_wp = WorkingPaper()
        with self.assertRaises(AuthError):
            self.wp_service.update_status(dummy_wp, "Review")

    def test_rbac_restores_after_login(self):
        """After session is restored, service calls must succeed again."""
        import uuid
        from security.auth import SessionToken
        from security.rbac import UserRole
        self.sm.current_session = None
        # Must fail without session
        with self.assertRaises(AuthError):
            self.client_service.create_client(name="Should Fail Corp")
        # Restore session
        self.sm.current_session = SessionToken(
            token_str="new_token", user_id=1,
            user_email="admin@test.com", role=UserRole.ADMINISTRATOR.value
        )
        # Must succeed with session — use unique name to avoid duplicate error
        unique_name = f"Restored Corp {uuid.uuid4().hex[:8]}"
        client = self.client_service.create_client(name=unique_name)
        self.assertIsNotNone(client.id)

    # --- DashboardService Unit Tests ---

    def test_dashboard_service_realtime_metrics(self):
        """DashboardService.get_realtime_metrics returns the expected keys."""
        from services.dashboard_service import DashboardService
        ds = DashboardService(self.session)
        metrics = ds.get_realtime_metrics()
        self.assertIn("total_clients", metrics)
        self.assertIn("completed_audits", metrics)
        self.assertIn("pending_reviews", metrics)
        self.assertIn("high_risk_cases", metrics)
        self.assertIn("recent_projects", metrics)
        self.assertIsInstance(metrics["total_clients"], int)

    def test_dashboard_service_client_cache(self):
        """load_client_name_cache returns name dict keyed by client ID."""
        from services.dashboard_service import DashboardService
        ds = DashboardService(self.session)
        cache = ds.load_client_name_cache({self.dummy_client.id})
        self.assertIn(self.dummy_client.id, cache)
        self.assertEqual(cache[self.dummy_client.id], "Test Client Corp")

    def test_dashboard_service_search(self):
        """search_clients_and_findings returns matching clients."""
        from services.dashboard_service import DashboardService
        ds = DashboardService(self.session)
        clients, findings = ds.search_clients_and_findings("Test Client")
        client_names = [c.name for c in clients]
        self.assertIn("Test Client Corp", client_names)

if __name__ == "__main__":
    unittest.main()
