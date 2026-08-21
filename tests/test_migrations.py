"""Unit tests for hand-rolled schema migration runner."""

import pytest

from finauditpro.infrastructure.persistence.migrations import MigrationRunner


def test_migration_runner_execution_and_idempotency(tmp_path) -> None:
    db_file = tmp_path / "test_migrations.db"
    runner = MigrationRunner(str(db_file))

    migrations = [
        (1, "create_test_table", "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);"),
        (2, "add_col_test_table", "ALTER TABLE test_table ADD COLUMN description TEXT;"),
    ]

    # First run
    count1 = runner.run_all(migrations)
    assert count1 == 2
    assert runner.get_applied_versions() == {1, 2}

    # Second run (Idempotency check)
    count2 = runner.run_all(migrations)
    assert count2 == 0
    assert runner.get_applied_versions() == {1, 2}


def test_migration_runner_transaction_rollback(tmp_path) -> None:
    db_file = tmp_path / "test_rollback.db"
    runner = MigrationRunner(str(db_file))

    bad_migration = [
        (1, "valid_step", "CREATE TABLE valid_table (id INT);"),
        (2, "failing_step", "INVALID SQL SYNTAX STATEMENT;"),
    ]

    with pytest.raises(RuntimeError):
        runner.run_all(bad_migration)

    # Version 1 succeeded, version 2 rolled back
    assert 1 in runner.get_applied_versions()
    assert 2 not in runner.get_applied_versions()
