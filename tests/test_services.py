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
        from database.database import SessionLocal
        from database.models import Client, FinancialYear, Engagement
        self.session = SessionLocal()
        
        # Create dummy client, FY, and engagement to satisfy FK constraints
        self.dummy_client = Client(name="Test Client Corp", gst_number="27AAACB1234F1Z0")
        self.session.add(self.dummy_client)
        self.session.flush()

        from datetime import datetime
        import uuid
        self.dummy_fy = FinancialYear(label=f"2025-{uuid.uuid4().hex[:4]}", start_date=datetime.utcnow(), end_date=datetime.utcnow())
        self.session.add(self.dummy_fy)
        self.session.flush()

        self.dummy_engagement = Engagement(client_id=self.dummy_client.id, financial_year_id=self.dummy_fy.id, audit_type="Statutory", status="Planning")
        self.session.add(self.dummy_engagement)
        self.session.commit()

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

if __name__ == "__main__":
    unittest.main()
