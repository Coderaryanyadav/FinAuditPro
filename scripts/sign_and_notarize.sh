#!/usr/bin/env bash
# ==============================================================================
# FinAuditPro — Code Signing, Notarization & DMG Packaging Script
#
# HONESTY NOTICE:
# This script is authored with official Apple codesign / notarytool workflow commands.
# Execution in this sandbox is BLOCKED: Requires Apple Developer ID certificate
# and Apple notarytool credentials (`KEYCHAIN_PROFILE` or `--apple-id`).
# DO NOT fake signature or claim notarization without valid Apple credentials.
# ==============================================================================

set -euo pipefail

# User Credential Placeholders — DO NOT commit real secrets
DEVELOPER_IDENTITY="${DEVELOPER_IDENTITY:-Developer ID Application: Your Firm Name (TEAMID)}"
KEYCHAIN_PROFILE="${KEYCHAIN_PROFILE:-AC_NOTARY_PROFILE}"
APP_PATH="dist/FinAuditPro.app"
DMG_PATH="dist/FinAuditPro-Installer.dmg"

echo "=== FinAuditPro macOS Code Signing & Notarization ==="

if [ ! -d "${APP_PATH}" ]; then
    echo "ERROR: ${APP_PATH} not found. Run scripts/build_app.sh first."
    exit 1
fi

echo "[1/4] Signing application bundle with Hardened Runtime..."
codesign --deep --force --options runtime --sign "${DEVELOPER_IDENTITY}" "${APP_PATH}"

echo "[2/4] Verifying code signature..."
codesign --verify --verbose "${APP_PATH}"

echo "[3/4] Creating DMG Installer..."
hdiutil create -volname "FinAuditPro" -srcfolder "${APP_PATH}" -ov -format UDZO "${DMG_PATH}"
codesign --force --sign "${DEVELOPER_IDENTITY}" "${DMG_PATH}"

echo "[4/4] Submitting to Apple Notary Service..."
echo "Running: xcrun notarytool submit ${DMG_PATH} --keychain-profile ${KEYCHAIN_PROFILE} --wait"
# xcrun notarytool submit "${DMG_PATH}" --keychain-profile "${KEYCHAIN_PROFILE}" --wait
# xcrun stapler staple "${APP_PATH}"

echo "Notarization Script Finished (Placeholder Mode)."
