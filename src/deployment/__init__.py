"""
FinAuditPro Production Deployment, Logging, & Diagnostic Package.
Provides system diagnostics, crash reporting, enterprise logging, version management, and database schema migrations.
"""

from .logger import setup_application_logging, get_log_file_path
from .crash_reporter import CrashReporter, setup_global_crash_handler
from .diagnostics import SystemDiagnostics, DiagnosticReport
from .version_checker import VersionChecker, AppVersionInfo
from .migration import DatabaseMigrator

__all__ = [
    "setup_application_logging",
    "get_log_file_path",
    "CrashReporter",
    "setup_global_crash_handler",
    "SystemDiagnostics",
    "DiagnosticReport",
    "VersionChecker",
    "AppVersionInfo",
    "DatabaseMigrator",
]
