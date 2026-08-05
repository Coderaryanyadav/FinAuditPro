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

## Verification Plan
- Run `pytest tests/ -v` after each fix to ensure no regressions.
- Manually inspect the code to ensure no fake numbers or `QMessageBox` lies remain.
