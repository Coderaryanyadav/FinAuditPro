# FinAuditPro — Client-Ready Delivery Plan

Clean up all test data, fix the first-run experience, and bring every broken flow into a working, production-quality state before client delivery.

---

## Problem Audit (What's Broken Right Now)

### Data Layer
- **All those "API Client Corp", "Encrypted DB Test Client", "Test Client Corp", "Default Audit Client" records** are sitting in the live database — the client will open the app and see ~18 garbage rows in Client Management.
- `src/ui/documents.py` **auto-creates a "Default Audit Client"** on first load if no project exists — this is a seed bomb that runs on every fresh install.
- `seed_admin.py` in root is a developer tool that should not ship with the project.

### First-Run User Flow (Completely Broken)
The app today has **no first-run detection**. When a client launches it fresh:
1. Splash → Login → Dashboard loads "Default Audit Client" in the header combo (leftover from documents.py auto-seed)
2. Dashboard KPI cards all show `0` but there's a phantom "Default Audit Client (FY 2025-26)" in the Active Audit selector — very confusing
3. Dashboard hero says "Good Morning, admin" — the user logged in as `admin@finauditpro.com`, a developer account
4. Client Management shows 18 test records
5. No **onboarding prompt** tells the user what to do first

### UI/UX Issues
- Dashboard **header greeting** works but the Active Audit dropdown is populated from the database — after data wipe it will be empty and crash `on_active_engagement_changed` if `data` is `None`/empty
- `documents.py::load_audit_projects` — if no projects exist, auto-creates "Default Audit Client" — this **must be removed**, replaced with an empty-state guidance message
- The `seed_admin.py` in root should be removed
- `AuditStatusDelegate.paint()` now fixed (QStyle.StateFlag.State_Selected), but the medium/high risk slices in the donut chart are 0 so the chart renders as just a green ring — needs a graceful empty-state label instead
- **Sidebar nav button active border** is missing a left-border 3px blue stripe (it only sets background color from QSS but no left-border override)

---

## User Flow (What It Should Be After Fix)

```
┌─────────────────────────────────────────────┐
│  1. Fresh Install                           │
│     → Splash (2s)                           │
│     → Login (admin@finauditpro.com / Admin@123) │
│     → Dashboard loads CLEAN                 │
│       - 0 clients, 0 audits                 │
│       - Active Audit: "No Active Audit"     │
│       - KPIs all show "0"                   │
│       - Table: empty-state row "No audit    │
│               projects yet — create one"    │
│       - Charts: empty / skeleton state       │
│  2. User clicks "Client Management"         │
│     → Clean empty list                      │
│     → "+ Add New Client" button             │
│  3. User adds first client                  │
│     → Clicks "+ New Audit" in header        │
│     → Selects that client                   │
│     → Dashboard refreshes with real data    │
└─────────────────────────────────────────────┘
```

---

## Proposed Changes

### 1. Wipe the Database (Remove All Test Data)
Remove the live `.db` file from AppData and let `init_db()` create a fresh schema on next boot.

#### [MODIFY] reset_db.py (NEW one-time script at project root)
Create a safe script to delete the encrypted DB and let the app start fresh.

---

### 2. Remove the Auto-Seed Bomb in documents.py

#### [MODIFY] [documents.py](file:///c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/documents.py)
Remove the `if not projects:` block that auto-creates "Default Audit Client" + AuditProject.
Replace with an empty-state message directing the user to Client Management first.

---

### 3. Remove seed_admin.py from root

#### [DELETE] seed_admin.py (developer-only tool, should not ship)

---

### 4. Fix Dashboard — Handle Empty State Gracefully

#### [MODIFY] [dashboard.py](file:///c:/Users/Jeet Shah/OneDrive/Desktop/1 - FinAuditPro/src/ui/dashboard.py)

- `populate_client_selector()` — if no clients/projects exist, add a placeholder item `"— No Active Audit —"` with `data=None` and skip `on_active_engagement_changed` when data is `None`.
- `on_active_engagement_changed()` — already has `if not data: return` guard, but it must also guard against the `"client_"` prefixed string being invalid.
- `_build_overview_page()` — add a prominent "Welcome Banner" when there are 0 clients: a sky-blue card saying "Welcome to FinAuditPro — Start by adding your first client."
- **Donut chart** — if `med == 0 and high == 0`, replace pie chart with a centered label "No Risk Data — Upload documents to begin risk analysis."
- **Greeting** — use `datetime.now()` to produce "Good Morning / Good Afternoon / Good Evening" correctly.

---

### 5. Fix Sidebar Active State Left Border

#### [MODIFY] [styles.py](file:///c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/styles.py)
Add `border-left: 3px solid #0284c7;` to `QPushButton#navButton[active="true"]` and compensate padding.

---

### 6. Re-seed Only the Admin User (No Client Data)

#### [MODIFY] seed_admin.py → becomes a clean `init_admin.py`
On first launch, `main.py` checks if any user exists. If 0 users → auto-create the admin account silently (no script needed). This way the app always has exactly one valid login credential ready.

#### [MODIFY] [main.py](file:///c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/main.py)
After `init_db()`, run a `_ensure_admin_user()` helper that creates `admin@finauditpro.com / Admin@123` only if no users exist.

---

### 7. Login Page — Show Hint Credentials on Fresh Install

#### [MODIFY] [login.py](file:///c:/Users/Jeet%20Shah/OneDrive/Desktop/1%20-%20FinAuditPro/src/ui/login.py)
Add a small `<i>Default login: admin@finauditpro.com / Admin@123</i>` caption in the form footer on first run (dev-mode hint).

---

## Verification Plan

### Manual Steps
1. Stop any running instance
2. Run `reset_db.py` to wipe database
3. Run `python src/main.py`
4. Verify: Splash → Login → Dashboard is fully empty and clean
5. Create a client, create an audit, see KPIs update
6. Verify no "Default Audit Client" or "API Client Corp" appears anywhere

### What Should NOT Break
- All Signal/Slot connections in dashboard.py
- `DashboardService.get_realtime_metrics()` — already handles 0 counts safely
- `AuditStatusDelegate.paint()` — already fixed with `QStyle.StateFlag.State_Selected`
- Login form and authentication flow
- All other pages (Documents, Clients, AI Analysis, etc.)

---

## Execution Order

1. Wipe DB → run `reset_db.py`  
2. Fix `documents.py` auto-seed removal  
3. Fix `main.py` admin auto-creation  
4. Fix `dashboard.py` empty-state handling + greeting  
5. Fix `styles.py` sidebar active border  
6. Fix `login.py` credential hint  
7. Re-launch and verify

> [!IMPORTANT]
> The database wipe will permanently delete all current records. Since these are all test records (API Client Corp, Encrypted DB Test Client, Test Client Corp, Default Audit Client), this is intentional and safe.
