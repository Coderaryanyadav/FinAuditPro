"""Automated language safety test ensuring zero occurrences of prohibited 'fraud' or 'fraudulent' terminology across the codebase."""

from pathlib import Path


def test_no_fraud_terminology_in_codebase() -> None:
    """Grep test enforcing ZERO occurrences of 'fraud' or 'fraudulent' in source code and analytics UI."""
    src_dir = Path("src/finauditpro")
    assert src_dir.is_dir()

    violations: list[tuple[str, int, str]] = []

    for py_file in src_dir.rglob("*.py"):
        lines = py_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            lowered = line.lower()
            # Ignore comments or docstrings explaining the rule if needed
            if "fraud" in lowered and "prohibited" not in lowered and "# ignore" not in lowered:
                violations.append((py_file.name, i, line.strip()))

    assert len(violations) == 0, (
        f"Found {len(violations)} prohibited 'fraud' terminology occurrences: {violations}"
    )
