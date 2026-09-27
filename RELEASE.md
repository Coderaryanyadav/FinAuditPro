# FinAuditPro Release Engineering & Distribution Guide (v1.2.0)

## 1. Release Architecture & Packaging
FinAuditPro is packaged as a standalone desktop binary for macOS, Windows, and Linux.

- **macOS:** Self-contained `.dmg` disk image built with PyInstaller and code-signed (`scripts/packaging/build_macos.py`).
- **Windows:** InnoSetup `.exe` installer (`scripts/packaging/build_windows.py`).
- **Linux:** Standalone AppImage / desktop binary.

## 2. Release Verification Workflow
1. **Automated Stress Testing:** Run 1,000 consecutive test passes:
   ```bash
   python3 scripts/development/run_1000_verifications.py
   ```
2. **Checksum Integrity Verification:** Validate SHA-256 package hashes:
   ```bash
   python3 scripts/packaging/verify_release.py
   ```

## 3. Documentation
For detailed release instructions, see [`docs/engineering/RELEASE.md`](docs/engineering/RELEASE.md) and [`docs/roadmap/CURRENT_PHASE.md`](docs/roadmap/CURRENT_PHASE.md).
