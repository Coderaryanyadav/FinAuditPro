# FinAuditPro — Production Release & Distribution

## 1. Desktop Packaging
FinAuditPro compiles into self-contained desktop distributions:
- **macOS:** `.dmg` installer with code signing (`scripts/packaging/build_macos.py`).
- **Windows:** InnoSetup `.exe` installer (`scripts/packaging/build_windows.py`).
- **Linux:** Standalone AppImage / desktop binary.

## 2. Release Verification
- Run 1,000 automated stress cycles: `python3 scripts/development/run_1000_verifications.py`.
- Validate SHA-256 checksums: `python3 scripts/packaging/verify_release.py`.
