#!/usr/bin/env bash
# ==============================================================================
# FinAuditPro — Standalone Application Bundle Build Script (macOS Apple Silicon)
#
# HONESTY NOTICE:
# This build script is authored and ready for execution.
# Execution in this sandbox is BLOCKED: PyInstaller is not installed in the offline venv.
# Run this script on a machine with PyInstaller installed (`pip install pyinstaller`).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== FinAuditPro Build Script ==="
echo "Project Root: ${PROJECT_ROOT}"

cd "${PROJECT_ROOT}"

if ! command -v pyinstaller &> /dev/null; then
    echo "ERROR: pyinstaller command not found."
    echo "Status: BLOCKED — PyInstaller cannot be installed offline without PyPI access."
    echo "To run this build script on a machine with internet access:"
    echo "  pip install -e .[ocr,ai] pyinstaller"
    echo "  bash scripts/build_app.sh"
    exit 1
fi

echo "Cleaning previous build artifacts..."
rm -rf build dist

echo "Running PyInstaller using finauditpro.spec..."
pyinstaller finauditpro.spec

echo "Build Complete! Output bundle: dist/FinAuditPro.app"
