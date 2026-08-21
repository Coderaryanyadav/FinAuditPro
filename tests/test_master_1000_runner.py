"""Automated test executing the master 1000-point E2E verification runner script."""

from scripts.run_1000_verifications import run_1000_verifications


def test_master_1000_verifications_runner() -> None:
    """Verify that the master E2E 1,000-point runner executes cleanly with 0 failures."""
    failures = run_1000_verifications()
    assert failures == 0, (
        f"Expected 0 failures in master 1000-point verification runner, got {failures}"
    )
