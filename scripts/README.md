# FinAuditPro Operational & Automation Scripts

This directory contains developer automation, diagnostic, packaging, and maintenance tooling:

```text
scripts/
├── README.md
├── development/
│   ├── auto_launch.py              # Zero-friction supervised background desktop launcher
│   ├── automated_system_check.py   # Launch-time system prerequisite and environment probe
│   └── run_1000_verifications.py   # Master 15-stage 1,000-point forensic audit runner
├── packaging/
│   ├── build_app.sh                # Standalone PyInstaller desktop binary builder
│   └── sign_and_notarize.sh        # macOS Apple code signing and notarization workflow
├── database/
│   └── reset_db.py                 # Development database reset and re-migration tool
└── maintenance/
    └── .gitkeep                    # Operational maintenance utilities
```

---

## Quick Reference

- **Run Automated Diagnostic Self-Check**:
  ```bash
  python scripts/automated_system_check.py
  # or python scripts/development/automated_system_check.py
  ```

- **Run 1,000-Point Forensic Lifecycle Suite**:
  ```bash
  python scripts/run_1000_verifications.py
  # or python scripts/development/run_1000_verifications.py
  ```

- **Launch Supervised Desktop Application**:
  ```bash
  python scripts/auto_launch.py
  ```
