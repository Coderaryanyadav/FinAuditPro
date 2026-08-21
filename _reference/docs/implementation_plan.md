# Implementation Plan: Fixing Fake Actions

This plan addresses the fake actions discovered in the sweep by either replacing them with real logic or honestly downgrading the UI copy where real logic isn't feasible yet.

## Goal Description
Fix 4 specific instances of UI buttons/actions that report fake success messages or display hardcoded data without performing real work.

## Proposed Changes

### 1. Dashboard Dark Mode Toggle
**Issue**: `toggle_theme()` in `src/ui/dashboard.py` toggles a variable and shows a success message but no dark mode stylesheet exists.
**Fix**: 
- Remove the "Theme Toggle" button from the settings menu and delete the `toggle_theme()` method. Implementing a full `DARK_QSS` is out of scope for this pass, and an honest UI should not have a button that does nothing.

### 2. Dashboard Notifications Popup
**Issue**: `show_notifications_popup()` in `src/ui/dashboard.py` hardcodes dates for GSTR-3B and CARO.
**Fix**: 
- Update `show_notifications_popup()` to query the `ComplianceTask` or `AuditProject` for any active deadlines. 
- If no data/deadlines are found (which is likely true since deadline tracking isn't fully wired), we will display a `QMessageBox.information` stating "No active alerts or upcoming deadlines for this engagement."

### 3. Compliance "Run Compliance Scan"
**Issue**: `run_compliance_scan()` in `src/ui/compliance.py` shows a fake success message. A full CARO 2020 / Form 3CD scan is not yet implemented in the `RuleEngine`.
**Fix**: 
- Downgrade the button text from "Run Full Compliance Scan" to "Reload Compliance Forms".
- Change the button behavior to simply reload the table data (or show "Forms reloaded") rather than claiming a scan completed successfully.

### 4. Compliance "Save Sign-offs"
**Issue**: `save_compliance_signoffs()` in `src/ui/compliance.py` claims to save but nothing persists.
**Fix**: 
- Since we don't have a `ComplianceSignoff` database model and I want to avoid risky Alembic migrations for a quick fix, I will rename the button to "Export Sign-offs (PDF)" and disable it with a tooltip saying "Feature coming in v2.0", OR I will change it to state "Sign-offs cannot be saved yet - requires database schema update".
- *Alternative*: I can add a `JSON` blob column to `AuditProject` if you really want persistence without full relations, but disabling/downgrading the button is safer for now.

## Open Questions
- For #4 (Save Sign-offs), do you prefer I completely remove the "Save Sign-offs" button, or disable it with a "Coming Soon" tooltip? I will plan to disable it with a tooltip to keep the UI layout intact.

#### [MODIFY] [reset_db.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/reset_db.py)
- Ensure script safely deletes active `.db` and `.db-journal` files and resets `.login_lockouts.json`.

#### [DELETE] [seed_admin.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/seed_admin.py)
- Remove root-level developer seed script since auto-provisioning is built into `src/main.py`.

#### [MODIFY] [src/main.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/main.py)
- Ensure `_ensure_admin_user()` runs after `init_db()` and `DatabaseMigrator.migrate()` to seamlessly seed `admin@finauditpro.com` on first launch.

---

### Component 2: Desktop UI Empty States & Polish

#### [MODIFY] [src/ui/dashboard.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/dashboard.py)
- In `populate_client_selector()`: Add placeholder item `"— No Active Audit —"` (`data=None`) when no clients/audits exist.
- In `on_active_engagement_changed()`: Guard against `data is None` or invalid selection strings to prevent crashes on empty DB.
- In Risk Donut Chart: When high and medium risk counts are 0, display a clean empty-state label `"No Risk Data — Upload documents to begin analysis"` instead of a plain empty ring.
- Header Greeting: Compute dynamic time-of-day greeting ("Good Morning", "Good Afternoon", "Good Evening").

#### [MODIFY] [src/ui/documents.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/documents.py)
- Confirm removal of auto-creation of "Default Audit Client". Show `"— No audit projects yet —"` when empty.

#### [MODIFY] [src/ui/styles.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/styles.py)
- Add `border-left: 3px solid #0284c7;` style to active navigation sidebar buttons (`QPushButton#navButton[active="true"]`).

#### [MODIFY] [src/ui/login.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/login.py)
- Add standard dev credential hint footer: `Default login: admin@finauditpro.com / Admin@123`.

---

### Component 3: Security & Statutory Compliance Hardening

#### [MODIFY] [src/rule_engine/rule_loader.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/rule_engine/rule_loader.py)
- Update `GSTMismatchRule` valid rates list to include statutory slabs: `[0.0, 0.1, 0.25, 1.5, 3.0, 5.0, 12.0, 18.0, 28.0]`.

#### [MODIFY] [api/dependencies.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/api/dependencies.py) & [src/core/config.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/core/config.py)
- Prevent silent fallback to known insecure JWT secret strings. Enforce runtime check or secure random key generation when env variable is missing in non-dev environments.

#### [MODIFY] [api/main.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/api/main.py)
- Adjust CORS middleware to avoid `allow_origins=["*"]` combined with `allow_credentials=True`.

#### [MODIFY] [tests/test_services.py](c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/tests/test_services.py)
- Reset `SecurityManager._instance = None` in test teardown to guarantee state isolation across test suites.

---

## Verification Plan
- Run `pytest tests/ -v` after each fix to ensure no regressions.
- Manually inspect the code to ensure no fake numbers or `QMessageBox` lies remain.
