"""
Unit Tests for FinAuditPro Reporting & Working Paper Engine.
Tests PDF Generation, Excel/CSV Exporter, ICAI Working Papers, Digital Signatures, and QR Verification.
"""

import unittest
import os
import tempfile

from reporting.report_engine import ReportEngine
from reporting.digital_signature import DigitalSignatureManager
from reporting.qr_verification import QRVerificationManager
from reporting.working_paper_engine import WorkingPaperEngine
from reporting.excel_export import ExcelReportExporter


class TestReportingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ReportEngine()
        self.sample_findings = [
            {
                "rule_id": "GST-001",
                "rule_name": "Missing Mandatory GSTIN",
                "category": "GST Rules",
                "severity": "HIGH",
                "risk_score": 75.0,
                "description": "Missing GSTIN on vendor invoice.",
                "recommendation": "Obtain valid GSTIN copy."
            }
        ]
        self.sample_wp = [
            {
                "working_paper_number": "WP-AUD-2026-001",
                "audit_area": "Revenue",
                "prepared_by": "CA User",
                "review_status": "APPROVED"
            }
        ]

    def test_digital_signature(self):
        sig = DigitalSignatureManager.create_signature_block(
            ca_name="CA Test User",
            membership_number="54321",
            firm_name="Test & Co",
            firm_registration_number="12345N"
        )
        self.assertEqual(sig.ca_name, "CA Test User")
        self.assertTrue(len(sig.digital_signature_hash) == 64)
        self.assertIn("UDIN PENDING", sig.udin)

    def test_qr_verification(self):
        payload = QRVerificationManager.generate_verification_payload(
            report_id="REP-001",
            client_name="TechCorp",
            gstin="27AAACB1234F1Z0",
            document_hash="hash123"
        )
        qr_str = QRVerificationManager.generate_qr_string(payload)
        self.assertTrue(qr_str.startswith("FINAUDITPRO://VERIFY?data="))

    def test_working_paper_engine(self):
        wp = WorkingPaperEngine.generate_working_paper(
            wp_number="WP-REV-01",
            audit_area="Revenue",
            prepared_by="Auditor",
            objective="Verify sales completeness",
            procedure="Sampled top 20 invoices"
        )
        self.assertEqual(wp.working_paper_number, "WP-REV-01")
        self.assertIn("Completeness", wp.assertions)

    def test_full_report_pack_generation(self):
        result = self.engine.generate_full_audit_pack(
            client_name="TechCorp Solutions",
            financial_year="2025-26",
            findings=self.sample_findings,
            working_papers=self.sample_wp
        )
        self.assertTrue(result.report_id.startswith("REP-"))
        self.assertEqual(result.client_name, "TechCorp Solutions")
        self.assertTrue(os.path.exists(result.pdf_path))


if __name__ == "__main__":
    unittest.main()
