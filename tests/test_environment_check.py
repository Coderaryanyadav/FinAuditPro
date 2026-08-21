"""Unit tests for launch-time environment prerequisite probes."""

import pytest
from finauditpro.infrastructure.environment_check import EnvironmentChecker


def test_python_version_check() -> None:
    """Verify Python runtime check returns PASS for Python 3.12+."""
    checker = EnvironmentChecker()
    item = checker.check_python_version()
    assert item.status == "PASS"
    assert "Python" in item.message


def test_data_directories_check(tmp_path, monkeypatch) -> None:
    """Verify data directories check returns PASS when folder is writable."""
    monkeypatch.setenv("FINAUDITPRO_DATA_DIR", str(tmp_path / "app_data"))
    checker = EnvironmentChecker()
    item = checker.check_data_directories()
    assert item.status == "PASS"


def test_full_environment_check_runs_without_crashing() -> None:
    """Verify run_all_checks returns complete EnvironmentStatusDTO with honest probes."""
    checker = EnvironmentChecker(lm_studio_base_url="http://invalid-localhost-url:9999")
    status_dto = checker.run_all_checks()
    assert status_dto is not None
    assert len(status_dto.items) >= 4
    # LM Studio probe should return WARN for invalid URL, not fake PASS
    lm_item = next(item for item in status_dto.items if "LM Studio" in item.name)
    assert lm_item.status in ("WARN", "FAIL")
