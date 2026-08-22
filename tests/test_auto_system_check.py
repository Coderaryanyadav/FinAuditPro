"""Automated test verifying the system check diagnostic script and auto-bootstrap launcher."""

from scripts.development.automated_system_check import run_system_check

from finauditpro.infrastructure.first_run import bootstrap_app_data_dirs, initialize_database


def test_automated_system_check_execution() -> None:
    """Verify that system diagnostic check executes cleanly with 0 failures."""
    failures = run_system_check()
    assert failures == 0, f"Expected 0 failures in system diagnostic check, got {failures}"


def test_first_run_auto_bootstrap(tmp_path) -> None:
    """Verify first-run auto-bootstrap creates directories and runs migrations."""
    db_dir, docs_dir, vector_dir, mpl_dir = bootstrap_app_data_dirs()
    db_manager = initialize_database()

    assert db_dir.exists()
    assert docs_dir.exists()
    assert vector_dir.exists()
    assert db_manager is not None
