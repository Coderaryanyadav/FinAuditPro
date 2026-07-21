# FinAuditPro Deployment Guide

This guide explains how to build, package, and release FinAuditPro for Windows, macOS, and Linux.

## Automated Release (CI/CD)

The easiest way to release FinAuditPro is via the automated GitHub Actions pipeline.

1. Ensure all changes are committed and pushed to `main`.
2. Run the release orchestrator script:
   ```bash
   python release.py --version 1.0.0
   ```
3. Push the new tag to GitHub:
   ```bash
   git push origin v1.0.0
   ```
4. GitHub Actions will automatically:
   - Build binaries using PyInstaller for Windows, macOS, and Linux.
   - Upload the artifacts to a new GitHub Release.

## Manual Build Process

If you need to build the application locally without GitHub Actions:

### Windows
1. Open PowerShell as Administrator.
2. Run the build script:
   ```powershell
   .\build.ps1
   ```
3. To create the setup wizard, open `scripts\installer.nsi` in NSIS compiler, or `scripts\installer.iss` in Inno Setup. This will generate `FinAuditPro-Setup.exe` in the `dist/` folder.

### macOS
1. Open Terminal.
2. Run the build script:
   ```bash
   ./build.sh
   ```
3. Create the deployable disk image (.dmg):
   ```bash
   ./scripts/create_dmg.sh
   ```

### Linux (Ubuntu)
1. Open Terminal.
2. Run the build script:
   ```bash
   ./build.sh
   ```
3. Package it into a portable AppImage:
   ```bash
   ./scripts/build_appimage.sh
   ```

## Release Verification Checklist

Before publishing a release publicly, test the generated artifacts:

- [ ] **Windows (.exe)**: Ensure it installs cleanly, creates a Start Menu shortcut, and launches without missing DLLs.
- [ ] **macOS (.dmg)**: Ensure the app can be dragged to `/Applications`. Check if code signing issues prevent launch (Gatekeeper).
- [ ] **Linux (.AppImage)**: Ensure it runs across different distributions without dependency errors (tested on Ubuntu 20.04+).
- [ ] **Offline Check**: Disable WiFi/Ethernet and ensure the application boots, logs in, and processes OCR using the fallback local engine.
- [ ] **Database Migration**: If upgrading from an older version, ensure the SQLite database migrations run seamlessly without data loss.
