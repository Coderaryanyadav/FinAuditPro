"""Unit tests for first-run app data directory bootstrap, Matplotlib setup, and DB initialization."""

import os

from finauditpro.infrastructure.first_run import bootstrap_app_data_dirs, initialize_database
from finauditpro.version import __version__, get_build_info


def test_version_info_validity() -> None:
    """Verify version info returns valid non-empty build metadata dictionary."""
    info = get_build_info()
    assert info["app_name"] == "FinAuditPro"
    assert info["version"] == __version__
    assert info["offline_isolated"] == "True"


def test_first_run_bootstrap_directories(tmp_path, monkeypatch) -> None:
    """Verify first-run bootstrap creates required directories and configures MPLCONFIGDIR."""
    test_data_dir = tmp_path / "app_data"
    monkeypatch.setenv("FINAUDITPRO_DATA_DIR", str(test_data_dir))

    db_dir, docs_dir, vector_dir, mpl_dir = bootstrap_app_data_dirs()

    assert db_dir.exists()
    assert docs_dir.exists()
    assert vector_dir.exists()
    assert mpl_dir.exists()
    assert os.environ.get("MPLCONFIGDIR") == str(mpl_dir)


def test_initialize_database_runs_all_migrations(tmp_path) -> None:
    """Verify initialize_database creates database and executes migrations 1 to 12 cleanly."""
    db_file = tmp_path / "bootstrap_test.db"
    db_manager = initialize_database(db_file)
    assert db_manager is not None

    with db_manager.session_scope() as session:
        # Check that migration history table exists and has 14 entries
        res = session.execute(
            __import__("sqlalchemy").text("SELECT COUNT(*) FROM schema_migrations")
        ).scalar()
        assert res == 14
