# FinAuditPro Release Engineering & Distribution Guide

This document describes the reproducible production release pipeline for **FinAuditPro** on macOS and Windows.

---

## 1. Overview & Release Artifacts

For each release tag (e.g. `v1.2.0`), the automated build system produces:

| Platform | Format | Artifact | Description |
| :--- | :--- | :--- | :--- |
| **macOS** | `.dmg` | `FinAuditPro-1.2.0-macOS-arm64.dmg` | Drag-and-drop installer with Applications shortcut and icon |
| **Windows** | `.exe` | `FinAuditPro-Setup-1.2.0-x64.exe` | Inno Setup standalone offline installer |
| **Windows (Portable)** | `.zip` | `FinAuditPro-1.2.0-Windows-x64.zip` | Standalone portable zero-install directory |
| **Checksums** | `.txt` | `SHA256SUMS.txt` | Cryptographic SHA-256 validation manifest |
| **Manifest** | `.json` | `release_manifest.json` | Machine-readable build provenance and metadata |

---

## 2. Runtime Path Architecture

FinAuditPro enforces strict physical separation between the **read-only application bundle** and **user-writable data directories**:

### Application Installation (Read-Only)
- **macOS**: `/Applications/FinAuditPro.app`
- **Windows**: `C:\Program Files\FinAuditPro\`

### User Data & Persistence (Writable)
- **macOS**: `~/Library/Application Support/FinAuditPro/`
  - `db/finauditpro.db` — SQLite 3.45+ relational database (WAL mode, foreign keys enabled)
  - `documents/` — Evidence vault and indexed working papers
  - `vector_store/` — FAISS local vector indices
  - `.secret_key.key` & `.secret_salt.bin` — Machine-derived column encryption keys
- **Windows**: `%APPDATA%\FinAuditPro\` (e.g. `C:\Users\<User>\AppData\Roaming\FinAuditPro\`)
- **Custom Location**: Set `FINAUDITPRO_DATA_DIR` environment variable to override data storage location.

---

## 3. Local Build Instructions

### Prerequisites
- Python 3.12+
- `pip install -e .[ocr,ai] pyinstaller`
- (macOS) `pip install dmgbuild`
- (Windows) [Inno Setup 6](https://jrsoftware.org/isinfo.php) (optional, for Setup.exe compilation)

### Building on macOS
```bash
# 1. Clean workspace
python scripts/packaging/clean.py

# 2. Run test suite & pre-build security audit
pytest tests/ -v
python scripts/packaging/verify_release.py --pre-build

# 3. Build .app bundle and .dmg installer
python scripts/packaging/build_macos.py
```
Output artifacts will be generated in `dist/`.

### Building on Windows
```powershell
# 1. Clean workspace
python scripts/packaging/clean.py

# 2. Run test suite & pre-build audit
pytest tests/ -v
python scripts/packaging/verify_release.py --pre-build

# 3. Build executable and installer
python scripts/packaging/build_windows.py
```

---

## 4. Code Signing & Apple Notarization

The build scripts are **signing- and notarization-ready**.

### macOS Developer ID Signing
Set the following environment variables on your build host:
```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Firm Name (TEAMID)"
export KEYCHAIN_PROFILE="AC_NOTARY_PROFILE"
```
When present, `scripts/packaging/build_macos.py` will sign the `.app` bundle with Apple Hardened Runtime (`--options runtime`) and timestamping.

---

## 5. Automated CI/CD Release Pipeline

FinAuditPro uses GitHub Actions (`.github/workflows/release.yml`) to automatically compile, verify, and publish releases.

### Triggering a Release
To publish a new production release:
1. Update version in `src/finauditpro/version.py` and `pyproject.toml`.
2. Commit and tag the commit:
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```
3. GitHub Actions will:
   - Run tests on macOS and Windows runners
   - Execute the pre-build security audit
   - Build native `.dmg` and `.exe` artifacts
   - Calculate master `SHA256SUMS.txt`
   - Publish a new GitHub Release with all binary attachments.

---

## 6. Release Notes Template (v1.2.0)

```markdown
### FinAuditPro v1.2.0 — Enterprise Audit Operating System

FinAuditPro is an offline-first, air-gapped audit intelligence platform tailored for Indian statutory audits, CARO 2020 compliance, and ICAI Standards on Auditing.

#### Highlights
- **100% Offline-First Architecture**: Zero data exfiltration; all evidence, analytics, and vector indices remain strictly local.
- **Precision Audit Matrix**: Automated SA 320 materiality calculation, risk-to-procedure mapping, and real-time finding promotion.
- **Deterministic Analytics Engine**: Benford's Law distribution analysis, duplicate payment clustering, and outlier detection.
- **Enterprise UI/UX**: Professional desktop application with high-DPI rendering, keyboard shortcuts, and dark/light palettes.
- **Tamper-Evident Working Papers**: Append-only audit trail with SHA-256 cryptographic seal.

#### System Requirements
- **macOS**: macOS 12.0 (Monterey) or later (Apple Silicon & Intel)
- **Windows**: Windows 10 / 11 (64-bit)

#### Verification & Integrity
Verify download integrity using SHA-256:
```bash
shasum -a 256 -c SHA256SUMS.txt
```
```
