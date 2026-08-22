#!/usr/bin/env bash
# ==============================================================================
# FinAuditPro — Dependency Exporter Utility
# Exports pyproject.toml / uv.lock dependencies to requirements.txt files
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "# ==============================================================================" > requirements.txt
echo "# GENERATED — DO NOT EDIT, run scripts/development/gen_requirements.sh" >> requirements.txt
echo "# ==============================================================================" >> requirements.txt
echo "" >> requirements.txt
uv export --no-hashes --format requirements-txt >> requirements.txt

echo "# ==============================================================================" > requirements-dev.txt
echo "# GENERATED — DO NOT EDIT, run scripts/development/gen_requirements.sh" >> requirements-dev.txt
echo "# ==============================================================================" >> requirements-dev.txt
echo "" >> requirements-dev.txt
echo "-r requirements.txt" >> requirements-dev.txt
uv export --no-hashes --all-groups --format requirements-txt | grep -v -F -f requirements.txt >> requirements-dev.txt || true

echo "✓ Successfully generated requirements.txt and requirements-dev.txt from pyproject.toml / uv.lock"
