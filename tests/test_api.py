"""
FastAPI Integration Test Suite for FinAuditPro API.
"""

import unittest
import sys
import os

# Ensure src/ is in sys.path
sys_path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(sys_path_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from fastapi.testclient import TestClient
from database.database import init_db, SessionLocal
from database.models import User, Client
from security.auth import PasswordHasher
from api.main import app

client = TestClient(app)


class TestFastAPIBackend(unittest.TestCase):

    def setUp(self):
        init_db()
        self.session = SessionLocal()

        # Seed test user
        self.test_username = "api_test_admin"
        self.test_password = "SecretAdminPassword123!"

        user = self.session.query(User).filter_by(username=self.test_username).first()
        if not user:
            user = User(
                username=self.test_username,
                email="admin@finauditapi.test",
                password_hash=PasswordHasher.hash_password(self.test_password),
                role="Administrator",
                is_active=True
            )
            self.session.add(user)
            self.session.commit()

        self.test_user = user

    def tearDown(self):
        self.session.close()

    def test_health_check(self):
        """GET /health returns 200 OK."""
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data.get("status"), "ok")

    def test_auth_login_and_unauthorized_access(self):
        """POST /auth/login returns JWT token, and unauthenticated requests return 401."""
        # Unauthenticated request should fail with 401
        res = client.get("/api/v1/clients")
        self.assertEqual(res.status_code, 401)

        # Login with valid credentials
        login_res = client.post("/api/v1/auth/login", json={
            "username": self.test_username,
            "password": self.test_password
        })
        self.assertEqual(login_res.status_code, 200)
        token_data = login_res.json()
        self.assertIn("access_token", token_data)
        token = token_data["access_token"]

        # Authenticated request should succeed with 200
        headers = {"Authorization": f"Bearer {token}"}
        authenticated_res = client.get("/api/v1/clients", headers=headers)
        self.assertEqual(authenticated_res.status_code, 200)
        self.assertIsInstance(authenticated_res.json(), list)

    def test_create_client_and_dashboard_metrics(self):
        """Create client via API and fetch dashboard metrics."""
        login_res = client.post("/api/v1/auth/login", json={
            "username": self.test_username,
            "password": self.test_password
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        import uuid
        c_name = f"API Client Corp {uuid.uuid4().hex[:6]}"
        create_res = client.post("/api/v1/clients", headers=headers, json={
            "name": c_name,
            "gst_number": "27AAACB1234F1Z0"
        })
        self.assertEqual(create_res.status_code, 201)
        created_client = create_res.json()
        self.assertEqual(created_client["name"], c_name)

        # Check metrics
        metrics_res = client.get("/api/v1/dashboard/metrics", headers=headers)
        self.assertEqual(metrics_res.status_code, 200)
        m_data = metrics_res.json()
        self.assertIn("total_clients", m_data)
        self.assertGreaterEqual(m_data["total_clients"], 1)

    def test_api_audit_logs_and_project_approval(self):
        """Test GET /dashboard/audit-logs and POST /audit-projects/{id}/approve."""
        login_res = client.post("/api/v1/auth/login", json={
            "username": self.test_username,
            "password": self.test_password
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check audit logs endpoint
        logs_res = client.get("/api/v1/dashboard/audit-logs", headers=headers)
        self.assertEqual(logs_res.status_code, 200)
        self.assertIsInstance(logs_res.json(), list)

    def test_api_token_revocation_on_logout(self):
        """Test token revocation persistence on POST /auth/logout."""
        login_res = client.post("/api/v1/auth/login", json={
            "username": self.test_username,
            "password": self.test_password
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Logout
        logout_res = client.post("/api/v1/auth/logout", headers=headers)
        self.assertEqual(logout_res.status_code, 200)

        # Subsequent request with revoked token should fail with 401
        res_after_logout = client.get("/api/v1/clients", headers=headers)
        self.assertEqual(res_after_logout.status_code, 401)
        self.assertIn("revoked", res_after_logout.json().get("detail", "").lower())


if __name__ == "__main__":
    unittest.main()
