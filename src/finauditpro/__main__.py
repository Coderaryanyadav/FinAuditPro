"""CLI entry point for FinAuditPro application."""

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Set High DPI scaling policy before importing ANY Qt modules that might trigger QGuiApplication creation
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

from finauditpro.infrastructure.ai.lmstudio_supervisor import LMStudioSupervisor
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.database import get_default_db_path
from finauditpro.ui.main_window import MainWindow


def main() -> None:
    """Initialize persistence and launch desktop GUI application."""
    parser = argparse.ArgumentParser(
        description="FinAuditPro — Offline-First Audit Operating System"
    )
    parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database file")
    parser.add_argument(
        "--headless", action="store_true", help="Initialize DB and exit without launching GUI"
    )
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else get_default_db_path()
    db_manager = initialize_database(db_path)

    if args.headless:
        print(f"Database initialized successfully at: {db_path}")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("FinAuditPro")
    app.setOrganizationName("FinAuditPro")

    window = MainWindow(db_manager)
    window.showFullScreen()

    exit_code = app.exec()

    # Graceful shutdown of resources
    print("Initiating graceful shutdown...")
    try:
        db_manager.shutdown()
        LMStudioSupervisor.stop_local_server()
    except Exception as e:
        print(f"Error during shutdown: {e}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
