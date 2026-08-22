# FinAuditPro — Application Packaging, Code Signing & Distribution Guide

This document details the production build, code signing, notarization, and DMG installer creation procedure for **FinAuditPro** on macOS Apple Silicon.

---

## 1. Environment & Build Status Posture

| Build Step | Status | Prerequisites / Blockers |
| :--- | :--- | :--- |
| **From-Source Launch** | `VERIFIED RUNNABLE` | Python 3.12+, `.venv` |
| **PyInstaller Bundle Build** | `AUTHORED (BLOCKED)` | Blocked in sandbox: PyInstaller package cannot be installed offline without PyPI network access. Script: `scripts/build_app.sh` |
| **macOS Code Signing** | `AUTHORED (BLOCKED)` | Blocked in sandbox: Requires Apple Developer ID Application Certificate. Script: `scripts/sign_and_notarize.sh` |
| **Apple Notarization & Stapling** | `AUTHORED (BLOCKED)` | Blocked in sandbox: Requires Apple ID & notarytool keychain profile. Script: `scripts/sign_and_notarize.sh` |
| **DMG Installer Creation** | `AUTHORED (BLOCKED)` | Requires built `.app` bundle and `hdiutil`. Script: `scripts/sign_and_notarize.sh` |

---

## 2. Production Build Execution Steps (For Connected Environment)

### Step 1: Install Build Dependencies
```bash
pip install -e .[ocr,ai] pyinstaller
```

### Step 2: Run PyInstaller Standalone Build
```bash
bash scripts/build_app.sh
```
This consumes `finauditpro.spec` and outputs `dist/FinAuditPro.app`.

### Step 3: Code Sign, Notarize, and Create DMG
Set your Apple Developer credentials and execute:
```bash
export DEVELOPER_IDENTITY="Developer ID Application: Your Firm Name (TEAMID)"
export KEYCHAIN_PROFILE="AC_NOTARY_PROFILE"

bash scripts/sign_and_notarize.sh
```
Output DMG: `dist/FinAuditPro-Installer.dmg`.
