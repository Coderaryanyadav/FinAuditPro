"""
Unit Tests for FinAuditPro Production Deployment & Diagnostics System.
Tests System Diagnostics, Logger Setup, Version Checker, and Database Migrations.
"""

import unittest
import os
import tempfile

from deployment.diagnostics import SystemDiagnostics
from deployment.logger import setup_application_logging, get_log_file_path
from deployment.version_checker import VersionChecker
from deployment.migration import DatabaseMigrator


class TestDeploymentSystem(unittest.TestCase):

    def test_system_diagnostics(self):
        report = SystemDiagnostics.run_diagnostics()
        self.assertIsNotNone(report.python_version)
        self.assertIsNotNone(report.operating_system)
        self.assertTrue(report.free_disk_space_gb > 0)

    def test_logging_setup(self):
        log_path = setup_application_logging()
        self.assertTrue(os.path.exists(log_path))

    def test_version_checker(self):
        ver_info = VersionChecker.get_version_info()
        self.assertEqual(ver_info.version, "1.0.0")
        self.assertTrue(ver_info.icai_compliant)

    def test_database_migrator(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            success = DatabaseMigrator.migrate(temp_db)
            self.assertTrue(success)
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)


if __name__ == "__main__":
    unittest.main()
