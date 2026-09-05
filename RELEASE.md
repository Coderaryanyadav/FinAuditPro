# FinAuditPro Release Engineering & Distribution Guide (v1.0.0)

This document provides the authoritative release engineering guide for maintainers building, packaging, and distributing **FinAuditPro**.

---

## 1. Single Source of Truth for Versioning
The canonical application version is defined in:
- `src/finauditpro/version.py`: `__version__ = "1.0.0"`
- `pyproject.toml`: `version = "1.0.0"`
- `finauditpro.spec`: `CFBundleVersion = "1.0.0"`
- `scripts/packaging/finauditpro.iss`: `#define MyAppVersion "1.0.0"`

---

## 2. Release Artifacts Overview
For each release tag (e.g. `v1.0.0`), the automated build system produces:

| Platform / Target | Format | Artifact | Description |
| :--- | :--- | :--- | :--- |
| **macOS (Apple Silicon & Intel)** | `.dmg` | `FinAuditPro-1.0.0-macOS-arm64.dmg` | Drag-and-drop installer bundle |
| **Windows (64-bit)** | `.exe` | `FinAuditPro-Setup-1.0.0-x64.exe` | Inno Setup standalone offline installer |
| **Windows (Portable)** | `.zip` | `FinAuditPro-1.0.0-Windows-x64.zip` | Standalone portable zero-install directory |
| **Python Wheel** | `.whl` | `finauditpro-1.0.0-py3-none-any.whl` | Standard Python wheel package |
| **Source Distribution** | `.tar.gz` | `finauditpro-1.0.0.tar.gz` | Standard source archive |
| **Cryptographic Checksums** | `.txt` | `SHA256SUMS.txt` | SHA-256 validation sums for all artifacts |
| **Release Manifest** | `.txt` | `RELEASE_MANIFEST_v1.0.0.txt` | Machine-readable build provenance and metadata |

---

## 3. Runtime Path & Security Architecture
FinAuditPro enforces strict physical separation between the **read-only application bundle** and **user-writable data directories**:

### Application Installation (Read-Only)
- **macOS**: `/Applications/FinAuditPro.app`
- **Windows**: `C:\Program Files\FinAuditPro\`

### User Data & Persistence (Writable)
- **macOS**: `~/Library/Application Support/FinAuditPro/`
  - `db/finauditpro.db` — SQLite 3.45+ relational database (WAL mode, foreign keys enabled)
  - `documents/` — Evidence vault and indexed working papers
  - `vector_store/` — FAISS local vector indices
- **Windows**: `%APPDATA%\FinAuditPro\` (e.g. `C:\Users\<User>\AppData\Roaming\FinAuditPro\`)
- **Custom Location**: Set `FINAUDITPRO_DATA_DIR` environment variable to override data storage location.

---

## 4. Local Build & Verification Pipeline

### Step 1: Clean Workspace
```bash
python scripts/packaging/clean.py
```

### Step 2: Full Test Suite & Static Analysis
```bash
python -m compileall -q src tests
pytest -q
ruff check src/ tests/ scripts/
mypy src/finauditpro
python scripts/packaging/verify_release.py --pre-build
```

### Step 3: Package Build
```bash
uv build
```

### Step 4: Standalone OS Installers (Optional / Platform-Specific)
- **macOS DMG**: `python scripts/packaging/build_macos.py`
- **Windows Setup**: `python scripts/packaging/build_windows.py`

### Step 5: Checksum Verification
```bash
shasum -a 256 dist/* > SHA256SUMS.txt
```

---

## 5. Code Signing & Apple Notarization
The build scripts are signing- and notarization-ready. Set the following environment variables on the signing host:
```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Firm Name (TEAMID)"
export KEYCHAIN_PROFILE="AC_NOTARY_PROFILE"
```
When configured, `scripts/packaging/build_macos.py` signs the `.app` bundle with Apple Hardened Runtime (`--options runtime`) and timestamps the binary.

---

## 6. GitHub Release Automation
To publish an official release:
1. Commit all verified changes to `main`.
2. Tag the release commit:
   ```bash
   git tag -a v1.0.0 -m "FinAuditPro v1.0.0"
   git push origin v1.0.0
   ```
3. GitHub Actions (`.github/workflows/release.yml`) builds multi-platform artifacts, computes checksums, and publishes the release.
4. User-facing release notes are maintained in [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).
