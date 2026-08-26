# FinAuditPro Operational & Automation Scripts

This directory contains developer automation, diagnostic, packaging, and maintenance tooling:

```text
scripts/
├── README.md
├── packaging/
│   ├── build_macos.py              # macOS .app bundle and polished .dmg builder
│   ├── build_windows.py            # Windows standalone .exe and Inno Setup installer builder
│   ├── clean.py                    # Workspace build cache and artifact purger
│   ├── generate_icons.py           # Multi-resolution icon (.icns / .ico / .png) generator
│   ├── verify_release.py           # Security credential scanner & SHA-256 manifest generator
│   └── finauditpro.iss             # Inno Setup Windows installer compiler configuration
├── development/
│   ├── auto_launch.py              # Zero-friction supervised background desktop launcher
│   ├── automated_system_check.py   # Launch-time system prerequisite and environment probe
│   └── run_1000_verifications.py   # Master 15-stage 1,000-point forensic audit runner
├── database/
│   └── reset_db.py                 # Development database reset and re-migration tool
└── maintenance/
    ├── retention_policy_sweep.py   # Audit document retention policy validator
    ├── vacuum_and_reindex.py       # SQLite database maintenance & reindexing
    └── verify_archive_integrity.py # Archive cryptographic seal verifier
```

---

## Packaging Quick Reference

- **Build macOS Bundle & DMG**:
  ```bash
  python scripts/packaging/build_macos.py
  ```

- **Build Windows Executable & Installer**:
  ```powershell
  python scripts/packaging/build_windows.py
  ```

- **Run Release Security & Checksum Verification**:
  ```bash
  python scripts/packaging/verify_release.py
  ```

- **Clean Build Artifacts**:
  ```bash
  python scripts/packaging/clean.py
  ```
