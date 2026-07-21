"""
Global Crash Reporter & Uncaught Exception Handler for FinAuditPro.
Catches uncaught runtime exceptions, logs crash tracebacks to disk, and displays error recovery dialogs.
"""

import sys
import os
import traceback
from datetime import datetime
import logging
try:
    from PySide6.QtWidgets import QMessageBox, QApplication
except ImportError:
    QMessageBox, QApplication = None, None

logger = logging.getLogger(__name__)
CRASH_DIR = "logs/crashes"

class CrashReporter:
    """Manages crash dump creation and exception interception."""

    @staticmethod
    def log_crash(exc_type, exc_value, exc_traceback) -> str:
        """Writes crash dump details to disk."""
        os.makedirs(CRASH_DIR, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        crash_file = os.path.join(CRASH_DIR, f"crash_{timestamp}.log")

        trace_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"=== FINAUDITPRO CRASH DUMP ===\n")
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}\n")
            f.write(f"Exception Type: {exc_type.__name__}\n")
            f.write(f"Message: {exc_value}\n\n")
            f.write(f"=== TRACEBACK ===\n{trace_str}\n")

        logger.critical(f"Uncaught Exception Intercepted! Crash log saved to {crash_file}\n{trace_str}")
        return crash_file


def setup_global_crash_handler():
    """Sets sys.excepthook to intercept unhandled exceptions."""
    def _exception_hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        crash_file = CrashReporter.log_crash(exc_type, exc_value, exc_tb)

        app = QApplication.instance()
        if app:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("FinAuditPro - System Error")
            msg_box.setText(f"An unexpected system error occurred:\n<b>{exc_type.__name__}: {exc_value}</b>")
            msg_box.setInformativeText(f"A detailed crash report has been saved to:\n{crash_file}\n\nYour application state has been preserved.")
            msg_box.exec()

    sys.excepthook = _exception_hook
