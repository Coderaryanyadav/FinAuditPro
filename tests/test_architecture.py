"""AST Architecture Enforcer verifying clean boundaries, file length limits, and import rules."""

import ast
from pathlib import Path


def get_all_python_files(root_dir: Path) -> list[Path]:
    return [p for p in root_dir.glob("**/*.py") if p.is_file() and not p.name.startswith(".")]


def test_file_line_count_limit() -> None:
    """Enforce that no single module exceeds 400 lines of code."""
    src_dir = Path(__file__).parent.parent / "src" / "finauditpro"
    py_files = get_all_python_files(src_dir)

    over_limit = []
    for py_file in py_files:
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        if line_count > 400:
            over_limit.append(f"{py_file.relative_to(src_dir)}: {line_count} lines")

    assert not over_limit, f"The following modules exceed the 400 line limit: {over_limit}"


def test_domain_layer_purity() -> None:
    """Enforce that domain/ imports zero external DB, UI, or application frameworks."""
    domain_dir = Path(__file__).parent.parent / "src" / "finauditpro" / "domain"
    py_files = get_all_python_files(domain_dir)

    forbidden_prefixes = (
        "sqlalchemy",
        "PySide6",
        "finauditpro.application",
        "finauditpro.infrastructure",
        "finauditpro.ui",
    )

    violations = []
    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(p) for p in forbidden_prefixes):
                        violations.append(f"{py_file.name}: imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if any(mod.startswith(p) for p in forbidden_prefixes):
                    violations.append(f"{py_file.name}: imports from '{mod}'")

    assert not violations, f"Domain layer architectural violations found: {violations}"


def test_ui_layer_isolation() -> None:
    """Enforce that ui/ imports zero persistence (sqlalchemy / infrastructure) modules directly."""
    ui_dir = Path(__file__).parent.parent / "src" / "finauditpro" / "ui"
    py_files = get_all_python_files(ui_dir)

    forbidden_prefixes = (
        "sqlalchemy",
        "finauditpro.infrastructure",
    )

    violations = []
    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(p) for p in forbidden_prefixes):
                        violations.append(f"{py_file.name}: imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if any(mod.startswith(p) for p in forbidden_prefixes):
                    violations.append(f"{py_file.name}: imports from '{mod}'")

    assert not violations, f"UI layer architectural violations found: {violations}"
