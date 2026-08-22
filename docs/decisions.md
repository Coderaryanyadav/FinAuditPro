# FinAuditPro — Architecture Decisions Record (ADR) & Build Log

## Product Design Transformation Architecture Decisions (Design.md)

### 1. Neutral-First Dark Design Tokens & Visual Hierarchy
- **Decision**: Centralized design tokens in `src/finauditpro/ui/theme.py` using layered dark surfaces (`#0f1117`, `#181b22`, `#222732`, borders `#2a303c`), strict typography scale, tabular financial figures, and semantic risk colors (Low: `#38bdf8`, Medium: `#f59e0b`, High: `#f97316`, Critical: `#ef4444`).
- **Rationale**: Replaced generic colorful card elements with a calm, high-density, professional desktop workspace ("Apple-level product design applied to professional audit software").

### 2. Grouped Information Architecture & Sidebar Navigation
- **Decision**: Redesigned sidebar into 4 audit workspace sections: `AUDIT WORKSPACE` (Dashboard, Firms, Clients, Engagements), `EVIDENCE & ANALYTICS` (Documents, Financial Data, Audit Matrix), `WORK & REVIEWS` (Working Papers, Reports, AI Copilot), and `OUTPUT & SYSTEM` (Archival, Roll-Forward, Settings).
- **Rationale**: Provides intuitive progressive disclosure and quick access without overwhelming the user with a flat list of buttons.

---

## Milestone 11: Packaging, Distribution & First-Run Architecture Decisions

### 1. Honest Packaging & Credential-Gated Status Posture
- **Decision**: Standalone PyInstaller build scripts (`scripts/build_app.sh`), spec file (`finauditpro.spec`), and code signing scripts (`scripts/sign_and_notarize.sh`) are authored to production standard. Because PyInstaller is not installed in the offline sandbox environment and Apple Developer ID credentials are absent, build execution is documented as `blocked: needs network access to install PyInstaller` and `blocked: needs Apple Developer ID credentials`.
- **Rationale**: Strict adherence to the product's zero fake functionality directive. A build script authored correctly and reported as unbuilt due to missing network/credentials maintains complete integrity. Zero fake `.app` bundles, zero fake hashes, and zero fake signatures.

### 2. Launch-Time Real Environment Diagnostics (No Fake "All Good")
- **Decision**: Implemented `EnvironmentChecker` performing real runtime probes for Python 3.12+ compatibility, Tesseract OCR executable pathing, LM Studio HTTP server reachability (`http://localhost:1234`), model load state, and directory writability.
- **Rationale**: Ensures the desktop application accurately reports prerequisite health and degrades features gracefully with clear remediation guidance when prerequisites are unpowered.
