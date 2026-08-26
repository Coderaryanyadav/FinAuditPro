#!/usr/bin/env python3
"""Clean all temporary build artifacts, distribution bundles, and caches."""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def clean_build_artifacts() -> None:
    """Remove build directories and caches."""
    print("🧹 Cleaning FinAuditPro build artifacts and caches...")

    dirs_to_remove = [
        PROJECT_ROOT / "build",
        PROJECT_ROOT / "dist",
        PROJECT_ROOT / ".pytest_cache",
        PROJECT_ROOT / ".mypy_cache",
        PROJECT_ROOT / ".ruff_cache",
        PROJECT_ROOT / "htmlcov",
    ]

    for d in dirs_to_remove:
        if d.exists():
            print(f"  Removing directory: {d.relative_to(PROJECT_ROOT)}")
            shutil.rmtree(d, ignore_errors=True)

    # Remove all __pycache__ and .pyc files
    for pyc_file in PROJECT_ROOT.rglob("*.pyc"):
        try:
            pyc_file.unlink()
        except Exception:
            pass

    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache, ignore_errors=True)
        except Exception:
            pass

    print("✓ Workspace is clean.")


if __name__ == "__main__":
    clean_build_artifacts()
