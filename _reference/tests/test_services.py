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
        from database.database import get_session
        from database.models import Client, FinancialYear, Engagement
        from datetime import datetime, timezone
        import uuid

        with get_session() as session:
            client = Client(name="Test Client Corp", gst_number="27AAACB1234F1Z0")
            session.add(client)
            session.flush()

            now_dt = datetime.now(timezone.utc)
            fy = FinancialYear(label=f"2025-{uuid.uuid4().hex}", start_date=now_dt, end_date=now_dt)
            session.add(fy)
            session.flush()

            eng = Engagement(client_id=client.id, financial_year_id=fy.id, audit_type="Statutory", status="Planning")
            session.add(eng)
            session.commit()

            self.dummy_client_id = client.id
            self.dummy_engagement_id = eng.id

        from database.database import SessionLocal
        self.session = SessionLocal()
        self.user_repo = UserRepository(self.session)
        self.client_repo = ClientRepository(self.session)
        self.doc_repo = DocumentRepository(self.session)
        self.wp_repo = WorkingPaperRepository(self.session)

        self.auth_service = AuthenticationService(self.user_repo)
        self.client_service = ClientService(self.client_repo)
        self.doc_service = DocumentService(self.doc_repo)
        self.wp_service = WorkingPaperService(self.wp_repo)

        from security.security_manager import SecurityManager
        from security.auth import SessionToken
        from security.rbac import UserRole
        self.sm = SecurityManager()
        self.sm.current_session = SessionToken(token_str="test_token", user_id=1, user_email="admin@test.com", role=UserRole.ADMINISTRATOR.value)

    def tearDown(self):
        self.sm.current_session = None
        from security.security_manager import SecurityManager
        SecurityManager._instance = None
        if hasattr(self, 'session') and self.session:
            self.session.close()

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

            doc = self.doc_service.upload_document(engagement_id=self.dummy_engagement_id, file_path=sample_file, document_type="Invoice")
            self.assertEqual(doc.file_name, "sample_invoice.pdf")
            self.assertIn(f"documents/eng_{self.dummy_engagement_id}", doc.file_path.replace("\\", "/"))
            self.assertTrue(os.path.exists(doc.file_path))

    def test_working_paper_service_index_creation(self):
        index = self.wp_service.create_index(engagement_id=self.dummy_engagement_id, section_code="REV-01", section_name="Revenue Audit")
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
            self.wp_service.create_index(engagement_id=self.dummy_engagement_id, section_code="TEST-01", section_name="Test")

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
        cache = ds.load_client_name_cache({self.dummy_client_id})
        self.assertIn(self.dummy_client_id, cache)
        self.assertEqual(cache[self.dummy_client_id], "Test Client Corp")

    def test_dashboard_service_search(self):
        """search_clients_and_findings returns matching clients."""
        from services.dashboard_service import DashboardService
        ds = DashboardService(self.session)
        clients, findings = ds.search_clients_and_findings("Test Client Corp")
        client_names = [c.name for c in clients]
        self.assertIn("Test Client Corp", client_names)

    def test_upload_audit_document_managed_storage_and_rbac(self):
        """upload_audit_document enforces RBAC and copies file to managed storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_file = os.path.join(temp_dir, "audit_doc.pdf")
            with open(sample_file, "wb") as f:
                f.write(b"%PDF-1.4 audit content")

            # Must succeed with active admin session
            doc = self.doc_service.upload_audit_document(audit_id=self.dummy_engagement_id, file_path=sample_file, doc_type="Audit Report")
            self.assertEqual(doc.file_name, "audit_doc.pdf")
            self.assertIn(f"documents/eng_{self.dummy_engagement_id}", doc.file_path.replace("\\", "/"))
            self.assertTrue(os.path.exists(doc.file_path))

            # Must fail when session is removed
            self.sm.current_session = None
            with self.assertRaises(AuthError):
                self.doc_service.upload_audit_document(audit_id=self.dummy_engagement_id, file_path=sample_file)

    def test_backup_engine_rbac_enforcement(self):
        """BackupEngine enforces PERFORM_BACKUP permission."""
        from security.backup import BackupEngine
        from security.auth import SessionToken
        from security.rbac import UserRole

        be = BackupEngine()
        # Non-admin role without PERFORM_BACKUP permission
        self.sm.current_session = SessionToken(
            token_str="read_only_token", user_id=2,
            user_email="read_only@test.com", role=UserRole.READ_ONLY.value
        )
        with self.assertRaises(AuthError):
            be.create_backup()

if __name__ == "__main__":
    unittest.main()

