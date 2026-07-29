# FinAuditPro — Brutal Full Project Audit

> **Auditor**: Principal Engineer + Staff UI/UX Designer + Security Engineer + Performance Engineer  
> **Codebase**: `c:\Users\Jeet Shah\OneDrive\Desktop\FinAuditPro`  
> **Commit**: `9d283f9` (main)  
> **Test Status at Audit Time**: 51/51 passing  
> **Date**: 2026-07-27

---

## 1. Project Understanding

### What the Application Does
FinAuditPro is an **offline-first desktop audit platform** for Chartered Accountants and statutory auditors in India. It automates the full audit lifecycle: client onboarding → document ingestion → AI-assisted analysis → compliance checks → working paper generation → official report export.

Key workflow:
1. CA logs in → selects client engagement
2. Uploads financial documents (PDFs, Excel, CSVs)
3. AI engine (Ollama + FAISS RAG) analyzes documents
4. Deterministic rule engine checks GSTIN, PAN, Benford's Law, Section 40A(3)
5. Findings are logged in working papers
6. SA 700/SA 705 audit reports are exported with SHA-256 hash and QR verification

### Main Technologies
| Layer | Technology |
|---|---|
| GUI | PySide6 6.7 (Qt for Python) |
| Database | SQLite (WAL mode), SQLAlchemy 2.0 |
| AI | Ollama REST API (llama3/deepseek-r1), FAISS, SentenceTransformers |
| OCR | PaddleOCR / EasyOCR / Tesseract (auto-detected) |
| PDF Export | `QPdfWriter` + `QTextDocument` |
| Security | PBKDF2-HMAC-SHA256, AES-256-GCM, SHA-256 hash chain audit log |
| Config | Pydantic `BaseSettings` |
| Background | `QThread` / `QRunnable` + `QThreadPool` |

### Architecture Overview
```
src/
├── main.py                    # Entry point
├── core/config.py             # Pydantic AppConfig singleton
├── ui/                        # All PySide6 screens (12 screens)
│   ├── dashboard.py           # Master controller + navigation (990 LOC)
│   ├── login.py               # Auth screen
│   ├── clients.py, documents.py, ai_analysis.py, reports.py, ...
│   └── styles.py              # Global QSS + EmptyState/Loading/Error widgets
├── services/                  # Business logic layer
├── database/
│   ├── models.py              # 18 SQLAlchemy ORM models
│   ├── database.py            # Engine, WAL config, get_session()
│   └── repositories/          # Repository pattern DAOs
├── security/
│   ├── auth.py                # SessionToken, PasswordHasher, AuthManager
│   ├── rbac.py                # 6 roles, 14 permissions
│   ├── security_manager.py    # Singleton facade
│   ├── crypto.py              # AES-256-GCM
│   └── audit_trail.py         # Immutable SHA-256 hash chain
├── ai/
│   ├── workers.py             # QThread / QRunnable workers
│   ├── ollama_client.py       # Ollama REST client
│   └── vector_store.py        # FAISS index
├── reporting/                 # PDF, Excel, digital signatures, QR
├── rule_engine/               # Deterministic statutory rules
├── document_intelligence/     # OCR pipeline, chunking, embeddings
├── analytics/                 # KPI, forecasting, charts engines
├── workflow/                  # Audit lifecycle state machine
└── deployment/                # Bootstrap, logging, migrations, crash reporting
```

### Data Flow
```
User → LoginWindow → AuthService → SecurityManager (session token)
     → DashboardWindow → [12 pages via QStackedWidget]
     → Document upload → OCR pipeline → FAISS embedding
     → Ollama LLM via OllamaWorker (QThread) → Finding saved to DB
     → Rule engine eval → Working papers
     → ReportsWidget → QPdfWriter + DigitalSignatureManager → PDF
```

### Authentication Flow
1. `LoginWindow.handle_login()` opens `get_session()` context
2. Looks up `User` by email → `UserRepository`
3. `AuthenticationService.login()` → `PasswordHasher.verify_password()` (PBKDF2)
4. Creates `SessionToken` via `AuthManager` → stored encrypted on disk
5. `SecurityManager.current_session` holds the active session (singleton)
6. RBAC permission checks via `RBACManager.has_permission(role, permission)`

**Critical gap**: The `login_successful` signal emits without passing the user/session object, so `DashboardWindow` has no reference to the authenticated user — it is effectively **stateless with respect to session**.

### Database Structure
18 models in `models.py`: `User`, `Client`, `ClientIndustry`, `KeyManagementPersonnel`, `FinancialYear`, `Engagement`, `AuditProject`, `AuditTeam`, `MaterialityCalculation`, `Document`, `Risk`, `ComplianceTask`, `WorkingPaperIndex`, `WorkingPaper`, `AuditProcedure`, `EvidenceLink`, `Finding`, `ReviewNote`, `DocumentPage`, `RiskProcedureLink`, `AuditReport`, `AuditLog`.

**Schema anomaly**: Both `Engagement` and `AuditProject` exist for overlapping concepts. `AuditProject` has a bare `financial_year` string column while `Engagement` uses a proper `FinancialYear` FK. This creates parallel, disconnected data models for the same concept.

### Third-Party Integrations
- **Ollama** (local, REST, `http://localhost:11434`) — no cloud
- **FAISS** (`faiss-cpu`) — local vector search
- **SentenceTransformers** — local embeddings
- **PaddleOCR / EasyOCR / Tesseract** — optional OCR (graceful degradation)
- **OpenPyXL** — Excel export
- **ReportLab** — PDF (though `QPdfWriter` is the primary export path)

### Deployment
- `install.bat` / `install.sh` — bootstrapper
- `FinAuditPro.spec` — PyInstaller spec for packaging
- Cross-platform data dir via `APPDATA` / `~/Library/Application Support` / `XDG_DATA_HOME`
- SQLite WAL mode configured on every connection

---

## 2. Architecture Audit

### A-1 — Dual Data Model for Engagements (`Engagement` vs `AuditProject`)
**Severity**: 🔴 Critical  
**Evidence**: `models.py` lines 104–126 (`Engagement`) and 128–139 (`AuditProject`)  
`Engagement` has a proper FK to `FinancialYear`, client, audit team, documents, risks, compliance tasks. `AuditProject` is a stripped parallel model with a plain string `financial_year` field. The UI predominantly uses `AuditProject` while the ORM models target `Engagement`. This means the rich relational data (teams, documents linked to engagement, risks) is invisible from the primary UI workflow.  
**Best Practice**: Consolidate into `Engagement`. Drop `AuditProject` or make it a view/alias.  
**Recommended Fix**: Migrate all UI queries from `AuditProject` to `Engagement`. Run a data migration.

### A-2 — `SecurityManager.current_session` Not Propagated to UI
**Severity**: 🔴 Critical  
**Evidence**: `main.py` line 47: `login.login_successful.connect(show_dashboard)`. The signal carries no arguments. `DashboardWindow.__init__` never receives the logged-in user.  
`dashboard.py` line 610: Hardcoded `"CA User"` name and `"Audit Partner"` role in the sidebar profile card. The actual authenticated user is invisible to the entire UI layer.  
**Best Practice**: Pass `SessionToken` or `User` to `DashboardWindow` constructor. Show real name and role.  
**Recommended Fix**: Change signal to `login_successful = Signal(object)`, emit the user, pass it to `DashboardWindow`.

### A-3 — `on_active_engagement_changed()` Silently Creates Phantom Audit Projects
**Severity**: 🔴 Critical  
**Evidence**: `dashboard.py` lines 921–928: When the selector shows a client without an existing project, selecting it creates a new `AuditProject` automatically with `status="Execution"` — without any user confirmation.  
**Best Practice**: This should open a creation dialog, not silently INSERT into the DB.

### A-4 — `reports.py::export_pdf()` References Undefined `self.client_combo`
**Severity**: 🔴 Critical  
**Evidence**: `reports.py` line 215: `self.client_combo.currentText()`. No `client_combo` widget is constructed anywhere in `ReportsWidget.__init__`. This will raise `AttributeError` on every PDF export.  
**Recommended Fix**: Use the already-loaded `client_name` variable instead.

### A-5 — DB Queries in Widget Constructors (Main Thread)
**Severity**: 🟠 High  
**Evidence**: `dashboard.py` lines 705–765: A full `with get_session()` block — including 7 SQL queries — executes inside `_build_overview_page()` which is called from `DashboardWindow.__init__`. This blocks the Qt event loop during startup.  
`ai_analysis.py` line 145: `self.load_active_document_view()` called in `__init__`.  
**Best Practice**: Defer all DB calls to `showEvent` or a `QTimer.singleShot(0, ...)` after `__init__`.

### A-6 — `AuditProjectsTableModel._load_client_cache()` Called Twice on Refresh
**Severity**: 🟡 Medium  
**Evidence**: `dashboard.py` lines 61–64 and 124–128: `_load_client_cache` is called in `__init__` and again on every `update_projects()` call. Each refresh opens a session and queries all clients unnecessarily.

### A-7 — `PlaceholderWidget` Referenced But Never Defined
**Severity**: 🟠 High  
**Evidence**: `dashboard.py` line 801: `return PlaceholderWidget(f"Unable to load {title}: {e}")`. `PlaceholderWidget` is not imported anywhere in `dashboard.py`. This would cause `NameError` at runtime if any page fails to load.

### A-8 — `src/data/` Directory in App Source Tree
**Severity**: 🟡 Medium  
**Evidence**: `src/data/` directory exists under source tree. Database and user files should live in user-writable locations (`APPDATA`), not alongside source code. The `core/config.py` correctly resolves platform dirs, but the `src/data/` dir signals confused separation.

---

## 3. Code Quality Audit

### Q-1 — Hardcoded CA Credentials in Production Templates
**Severity**: 🔴 Critical  
**Evidence**: `reports.py` lines 160–162: `M/S SHARMA & ASSOCIATES`, `FRN: 109876W`, `CA Rajesh Sharma`, membership `012345`. These are placeholder credentials baked into every exported official report. Users cannot configure their firm details from the UI.  
**Recommended Fix**: Add a Settings screen field for CA firm name, membership number, FRN. Load from `SecureStorage`.

### Q-2 — Hardcoded Default Credentials in Login Screen
**Severity**: 🔴 Critical  
**Evidence**: `login.py` lines 119, 126: `self.email_input.setText("admin@finauditpro.com")` and `self.password_input.setText("admin123")`. Default credentials are displayed and pre-filled in the UI — and the same default is seeded into the DB (`login.py` lines 219–227).  
**Best Practice**: Never pre-fill password fields. Seed admin accounts only via CLI/setup scripts.

### Q-3 — Bare `except Exception` Silently Swallows Errors in Reports
**Severity**: 🟠 High  
**Evidence**: `reports.py` lines 143–146: `except Exception: client_name = "Sample Client Pvt Ltd"`. Any database failure silently substitutes demo data into official audit reports without alerting the user.

### Q-4 — `ai_analysis.py::on_ai_chunk()` Uses `findChild(QLabel)` Pattern
**Severity**: 🟠 High  
**Evidence**: `ai_analysis.py` lines 279–282. Finding the label child via `findChild` is fragile — if the bubble layout changes, this breaks silently. The bubble frame should expose a `setText()` API directly.

### Q-5 — Chart in `AuditProgressChart` Uses Hardcoded Months/Data
**Severity**: 🟠 High  
**Evidence**: `dashboard.py` lines 370–375: `months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]` and `data_points = [12, 18, 15, 25, 22, 28]`. The chart only partially replaces these from real data (first 6 projects). Months are always Jan–Jun regardless of the current year.

### Q-6 — `toggle_theme()` Shows Message Box Instead of Applying Theme
**Severity**: 🟡 Medium  
**Evidence**: `dashboard.py` lines 955–959: The dark mode button toggles a bool and shows an `information()` dialog. No actual QSS dark theme is applied. This is a placeholder that misleads users.

### Q-7 — `show_notifications_popup()` Contains Hardcoded Demo Alerts
**Severity**: 🟡 Medium  
**Evidence**: `dashboard.py` lines 978–986: "GSTR-3B Tax Filing Deadline: 5 days remaining" is a hardcoded string in a `QMessageBox`, not a real notification from the DB.

### Q-8 — Single-Letter Variable Names Throughout UI Code
**Severity**: 🟡 Medium  
**Evidence**: `ai_analysis.py` lines 45–83: `v`, `h1`, `h2`, `b`, `t`, `d`, `ev`, `ev_l`, `ev_t`, `ev_d` — these are layout and widget variables with no descriptive names. Deeply nested, unreadable.

### Q-9 — `Document.ocr_confidence` Defaults to `98.5` (Fabricated Value)
**Severity**: 🟠 High  
**Evidence**: `models.py` line 177: `ocr_confidence = Column(Float, default=98.5)`. Every document inserted shows 98.5% OCR confidence even if OCR was never run on it. This is fake data displayed as genuine metrics.

### Q-10 — `AuditProject` and `Engagement` Both FK to `Client` with No Constraint
**Severity**: 🟡 Medium  
**Evidence**: `models.py` lines 131 and 107. Duplicate client references across two overlapping models with no referential integrity between them.

### Q-11 — `login.py::handle_login()` Still Uses Raw String Comparison for `is_active`
**Severity**: 🟡 Medium  
**Evidence**: `auth_service.py` lines 56–57: The active check happens AFTER password verification and session creation have already been called — if a deactivated user knows their password, the session is already created before the guard runs.

### Q-12 — `refresh_realtime_data()` Called on Every Navigation Click
**Severity**: 🟡 Medium  
**Evidence**: `dashboard.py` line 849: `self.refresh_realtime_data()` is called in `_on_nav_click()` for every tab switch. Navigating to Settings runs 4 database queries unnecessarily.

---

## 4. Error / Runtime Audit

### E-1 — `self.client_combo` AttributeError on Every PDF Export
**Severity**: 🔴 Critical | **Likelihood**: 100% | **Impact**: Complete export failure  
**Evidence**: `reports.py` line 215 — `self.client_combo` is never defined.

### E-2 — `PlaceholderWidget` NameError
**Severity**: 🔴 Critical | **Likelihood**: Whenever any page crashes during load | **Impact**: App crash  
**Evidence**: `dashboard.py` line 801.

### E-3 — `AuthenticationService.logout()` Does Not Revoke Session Token
**Severity**: 🟠 High | **Likelihood**: Every logout | **Impact**: Session token remains valid on disk after logout  
**Evidence**: `auth_service.py` lines 73–75: `logout()` sets `self.current_user = None` but never calls `auth_manager.revoke_session(token_str)`. The encrypted `.active_sessions.dat` file still contains the valid token.

### E-4 — Race Condition: `OllamaWorker` Not Stopped Before Navigation
**Severity**: 🟠 High | **Likelihood**: Medium (user navigates away during LLM response) | **Impact**: Crashes, double-rendering  
**Evidence**: `ai_analysis.py` line 256: `self.worker = None`. When the user navigates away and back, the old `OllamaWorker` thread is still running and emitting `chunk_received` into now-stale UI elements.

### E-5 — SQLite `mmap_size=30000000000` (30 GB)
**Severity**: 🟠 High | **Likelihood**: On machines with <32GB RAM | **Impact**: OS mmap failure, SQLite errors  
**Evidence**: `database.py` line 48. On typical 8–16GB RAM machines, this PRAGMA sets an absurdly large mmap size. SQLite will not actually allocate this, but it's a misconfigured value clearly copied from an M4 Pro test machine comment.

### E-6 — `findings` Accessed Outside Session in `load_report_draft()`
**Severity**: 🟠 High | **Likelihood**: Medium | **Impact**: `DetachedInstanceError`  
**Evidence**: `reports.py` lines 136–142: `findings` list is used inside `with get_session()` but the ORM objects may be lazy-loaded. If `Finding.description` triggers a lazy load after the session closes, SQLAlchemy raises `DetachedInstanceError`.

### E-7 — `AuditProgressChart` Data Points Access `p.status` After Session Close
**Severity**: 🟡 Medium | **Likelihood**: Low | **Impact**: `DetachedInstanceError`  
**Evidence**: `dashboard.py` line 374: `data_points[idx] = 100 if p.status == "Completed"`. The `projects` list is passed from a closed session; accessing attributes on detached instances can fail without `expire_on_commit=False`.

### E-8 — No Input Validation on UDIN Field
**Severity**: 🟡 Medium | **Likelihood**: High (user typos) | **Impact**: Invalid UDIN on official exported reports  
**Evidence**: `reports.py` line 87: `self.udin_input.setText("25012345AAAAAA1234")`. UDIN format: `YYMembershipNoAlphaNumeric`. No regex validation before export.

### E-9 — `populate_client_selector()` Called Every Time Dialog Closes
**Severity**: 🟡 Medium | **Likelihood**: Every new audit creation | **Impact**: Unnecessary DB round-trips  
**Evidence**: `dashboard.py` line 897.

### E-10 — Memory Leak: Chat Bubbles in `AIAuditWidget` Never Cleared
**Severity**: 🟡 Medium | **Likelihood**: Long sessions | **Impact**: Unbounded widget accumulation in `self.chat_layout`  
**Evidence**: `ai_analysis.py` line 307: `self.chat_layout.addWidget(bubble_frame)`. There is no limit or cleanup on the number of chat bubbles.

---

## 5. UI Audit (Page-by-Page)

### Login Screen — Score: 7/10
**Strengths**: Clean split-panel layout, gradient left panel, well-spaced form.  
**Issues**:  
- ❌ Password pre-filled (`"admin123"`) — major security UX problem  
- ❌ Email pre-filled — reduces the illusion of security  
- ❌ Role selector is redundant — users select their role at login? Roles should come from DB.  
- ❌ "Forgot Password?" leads to a message box telling users to contact sysadmin — useless UX  
- ❌ No keyboard focus order: Tab order is not set; pressing Tab after email field may not land on password  
- ✅ Show/hide password toggle present  
- ✅ "Signing In..." button disable feedback  

**Improvement**: Remove pre-filled credentials. Remove role selector (look up role from DB). Add proper focus chain.

### Dashboard Overview — Score: 6/10
**Strengths**: KPI cards look polished. Spline chart and donut chart add visual richness. QTableView with custom delegate is properly engineered.  
**Issues**:  
- ❌ "Good Morning, Auditor" — static greeting never updates for time of day or actual username  
- ❌ Chart uses hardcoded Jan–Jun months  
- ❌ Notification popup contains hardcoded dummy alerts  
- ❌ Dark mode button triggers a message box instead of changing theme  
- ❌ Search bar is purely cosmetic — no search logic wired  
- ❌ Profile card shows "CA User / Audit Partner" regardless of who is logged in  

### AI Analysis — Score: 6/10
**Strengths**: 3-column split view is well designed. Prompt library chips are a smart feature. Token streaming is properly off main-thread.  
**Issues**:  
- ❌ "🟢 Ollama Local RAG Engine Active" badge is always green regardless of Ollama connection status  
- ❌ Chat history grows infinitely with no scroll-to-bottom or clear function  
- ❌ No "thinking" indicator while LLM generates  
- ❌ Document panel always shows last-uploaded document — no way to select a specific document  

### Reports Screen — Score: 5/10
**Strengths**: WYSIWYG preview with real SHA-256 hash is good.  
**Issues**:  
- ❌ Hardcoded CA firm name "M/S SHARMA & ASSOCIATES" in every exported report  
- ❌ Export will crash due to `self.client_combo` AttributeError  
- ❌ UDIN field has no validation  
- ❌ No date stamp on the report (FY 2024-25 hardcoded)  
- ❌ No print/preview button separate from export  

### Clients Screen — Score: 7/10
**Strengths**: Table-based client list, create/edit dialog.  
**Issues**:  
- ❌ No search/filter on client list  
- ❌ No bulk import from CSV/Excel  
- ❌ Deleting a client with active engagements is not warned  

### Working Papers — Score: 7/10
**Strengths**: SA 230 reference, engagement-scoped.  
**Issues**:  
- ❌ No diff view between draft and reviewed versions  
- ❌ No approval workflow signature  

### Settings — Score: 5/10
**Issues**:  
- ❌ No field for CA firm name / membership no. — these are needed for reports  
- ❌ No Ollama model selector (hardcoded `llama3` assumption)  
- ❌ No session timeout configuration in UI  

---

## 6. UX Audit

### UX-1 — No Onboarding / First-Run Wizard
New users land on an empty dashboard with no guidance. No prompt to add first client, no sample data, no walkthrough. The AI panel shows "No Document Indexed" with no actionable next step highlighted.

### UX-2 — Role Selection at Login Is Confusing
The role combo in `LoginWindow` lets users claim any role. A Junior Auditor can select "Audit Partner (Full Access)" — the DB role is what actually controls RBAC, not this dropdown. This UI element is misleading and should be removed.

### UX-3 — Search Bar Is Non-Functional
The global search bar in the header accepts input but produces zero results. Users will attempt to use it and get nothing.

### UX-4 — No Confirmation on Destructive Actions
Deleting documents, clients, or findings shows no confirmation dialog in the current code patterns seen. Accidental deletions are unrecoverable.

### UX-5 — Navigation Mismatch: Sidebar Index vs Page Index
`dashboard.py` lines 803–837: Working Papers is navigation index 11 (sidebar btn 11) but in the `nav_buttons` list it is also 11 — this is fragile. The table double-click `stacked_widget.setCurrentIndex(11)` on line 852 is a hardcoded magic number.

### UX-6 — No Feedback After Working Paper Save
`ai_analysis.py` line 377 shows a `QMessageBox.information` but this is the only feedback — no list refresh, no visual indicator on the finding card that it was saved.

### UX-7 — Engagement Switching Has No Confirmation
Changing the active engagement combo instantly queries the DB and potentially creates new projects silently.

### UX-8 — AI Badge Always Shows Green "Active" Status
`ai_analysis.py` line 110: "🟢 Ollama Local RAG Engine Active" — even when Ollama is offline. Should be dynamically checked (ping endpoint on widget show).

---

## 7. Performance Audit (Ranked by Impact)

### P-1 — DB queries in `__init__` / widget construction (HIGH IMPACT)
7+ SQL queries run on the main thread during `DashboardWindow.__init__`. Startup latency directly scales with DB size. Use `QTimer.singleShot(0, self._load_data)` to defer.

### P-2 — `mmap_size=30_000_000_000` (30 GB) SQLite PRAGMA (HIGH IMPACT)
`database.py` line 48. On 8–16 GB machines the OS will clamp this, but it wastes time mapping. Set to 256 MB: `PRAGMA mmap_size=268435456`.

### P-3 — No Lazy Loading of Screen Pages (MEDIUM IMPACT)
`DashboardWindow._build_stacked_pages()` instantiates ALL 12 screen widgets at startup. Even if the user never visits "GST Verification", that widget runs its `__init__` (including DB queries). Use on-demand creation.

### P-4 — `refresh_realtime_data()` Called on Every Nav Click (MEDIUM IMPACT)
Runs 4 SQL queries + model reset on every sidebar click. This is unnecessary for navigating to Reports or Settings.

### P-5 — Chat Bubbles Accumulate Without Limit (MEDIUM IMPACT)
`ai_analysis.py`: Each `add_message()` adds a new `QFrame` with `QLabel` children to the chat layout. After 50+ messages, layout recalculation becomes expensive.

### P-6 — `populate_client_selector()` Queries Clients + Projects N+1 (MEDIUM IMPACT)
`dashboard.py` lines 903–914: For each client, a separate `session.query(AuditProject).filter_by(client_id=c.id).all()` is executed — classic N+1. Should be a single JOIN query.

### P-7 — Document RAG context truncated to 1500 chars (LOW IMPACT, but quality issue)
`ai_analysis.py` line 316: `f.read(1500)`. Only 1500 chars of document context is fed to the LLM. A typical trial balance has >10,000 chars of meaningful content.

---

## 8. Security Audit

### S-1 — Hardcoded Default Credentials Seeded Into DB
**Severity**: 🔴 Critical  
**Evidence**: `login.py` lines 219–227: `password_hash=PasswordHasher.hash_password("admin123")`. Default admin account with password `admin123` is auto-created on first run. Any user who knows this can log in.  
**Mitigation**: Force password change on first login. Remove pre-filled credentials from UI.

### S-2 — `AuthenticationService.logout()` Does Not Revoke Disk Session
**Severity**: 🟠 High  
**Evidence**: `auth_service.py` lines 73–75. Session token remains in `.active_sessions.dat`.  
**Mitigation**: Call `self.security_manager.auth_manager.revoke_session(token_str)` in `logout()`.

### S-3 — `SecurityManager.current_session` Allows UI Bypass
**Severity**: 🟠 High  
**Evidence**: `dashboard.py` lines 878–880: `if sm.current_session and not sm.check_permission(...)`. If `sm.current_session` is `None` (e.g., after session expiry), the RBAC check is SKIPPED entirely. Correct logic: if no session, deny access.  
**Mitigation**: Change to `if not sm.current_session or not sm.check_permission(...)`.

### S-4 — UDIN Field Accepts Arbitrary Input on Official Reports
**Severity**: 🟡 Medium  
UDIN is a mandatory ICAI regulatory identifier. Exporting a report with an invalid/fake UDIN is a regulatory compliance violation.  
**Mitigation**: Validate format: `^[0-9]{8}[A-Z]{6}[A-Z0-9]{4}$`.

### S-5 — `PasswordHasher.ITERATIONS` Default of 600,000 is Excellent (Strength)
PBKDF2 at 600k iterations far exceeds OWASP 2023 minimum (210,000). This is correctly implemented.

### S-6 — `SessionToken.user_email` Field Used as Role/Auth Reference
**Severity**: 🟡 Medium  
`SessionToken.to_dict()` serializes the full email. If the session file is somehow read (even though AES encrypted), the email is exposed. Consider hashing or omitting from serialized form.

### S-7 — No Rate Limiting on Login Attempts
**Severity**: 🟠 High  
`login.py::handle_login()` has no attempt counter, lockout, or delay. Brute force against local DB is trivially possible. Offline app mitigates risk slightly, but insider threat remains.  
**Mitigation**: Add exponential backoff (1s, 2s, 4s) after 3 failed attempts. Lock after 10.

### S-8 — Audit Log `ip_address` Column Always Null
**Severity**: 🟡 Medium  
**Evidence**: `models.py` line 342. No IP logging is done in `ImmutableAuditLogger`. For a desktop app this is acceptable, but the column implies it's tracked.

### S-9 — `AESCryptoEngine` Key Derivation Not Verified
**Evidence**: `security/crypto.py` is used in auth.py. AES-256-GCM is referenced in `security_manager.py`. The key management and rotation story is not visible. If the derived key changes (e.g., new install), all sessions become unreadable — but there's no graceful handling beyond silently clearing sessions.

---

## 9. Accessibility Audit

### ACC-1 — No `setTabOrder()` Called Anywhere
No `setTabOrder()` is called in any widget. Login form Tab key behavior is undefined — Qt auto-assigns but this is not guaranteed correct across platforms.

### ACC-2 — No Accessible Names / ARIA Equivalent
`setAccessibleName()` and `setAccessibleDescription()` are not used on any interactive element. Screen readers (NVDA, JAWS) will describe all buttons as "button" with no context.

### ACC-3 — Emoji Used as Primary Icons
Sidebar uses emoji icons (`📊`, `🏢`, `📁`). Emoji rendering varies across platforms and is not accessible to screen readers as meaningful content.

### ACC-4 — Color Used as Sole Differentiator (Risk Levels)
Risk dots in the table delegate use color only (`#10b981` green / `#f59e0b` yellow / `#ef4444` red). No shape, pattern, or text supplement. WCAG 2.1 § 1.4.1 violation.

### ACC-5 — Insufficient Color Contrast in Some Labels
`#94a3b8` (slate-400) on `#f8fafc` (white-ish background) = ~2.8:1 contrast ratio. WCAG AA minimum is 4.5:1 for normal text, 3:1 for large text. Multiple subtitle labels fail this.

### ACC-6 — No Focus Rings Visible
`QPushButton#navButton` QSS doesn't define `QPushButton#navButton:focus`. Keyboard users have no visible focus indicator.

### ACC-7 — `QMessageBox` Used for All Dialogs
Non-destructive information dialogs mixed with critical error dialogs all use `QMessageBox`. No visual hierarchy difference for the user (aside from icon).

---

## 10. Design System Audit

### DS-1 — Inconsistent Button Styles (8+ Inline Variants)
Buttons defined inline with `setStyleSheet()` across files:
- Primary: `background-color: #0ea5e9; color: white` (dashboard.py, reports.py, clients.py)
- Secondary: `background-color: #f1f5f9; color: #0284c7` (reports.py)
- Danger: `background-color: #ef4444` (some screens)
- Outline: `border: 1px solid #cbd5e1` (some screens)

`styles.py` defines `QPushButton#primaryButton`, `#secondaryButton`, `#outlineButton` in the global QSS — but most widgets set inline styles instead of using `setObjectName()`. The design system is defined but not adopted.

### DS-2 — Typography Is Not Consistently Applied
`styles.py` defines the global font family as `Inter`. But individual labels override with raw pixel sizes via inline `setStyleSheet()`. No typographic scale is defined (e.g., `--text-xs: 11px`, `--text-sm: 12px`, etc.).

### DS-3 — Spacing Is Ad-Hoc
`setContentsMargins(32, 24, 32, 32)`, `setContentsMargins(16, 14, 16, 14)`, `setContentsMargins(24, 0, 24, 0)` — different numbers in every layout with no shared constant.

### DS-4 — Icon Strategy Is Incoherent
Sidebar uses emoji. Some headers use emoji. The `MetricCard` uses emoji. There is no SVG icon library, no Qt resource file with icons. This is fine for a prototype but looks inconsistent and has accessibility issues.

### DS-5 — Color Palette Is Defined Implicitly
~15 distinct colors are used across files but never defined as named constants. `#0ea5e9`, `#0284c7`, `#0369a1`, `#10b981`, `#f59e0b`, `#ef4444`, `#64748b`, etc. are scattered as hex literals.

**Recommended fix**: Define a `theme.py` constants file:
```python
class Colors:
    PRIMARY = "#0ea5e9"
    PRIMARY_DARK = "#0284c7"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    SURFACE = "#f8fafc"
```

---

## 11. Product Audit

### What Makes the Product Stand Out
- **True air-gapped design**: No cloud dependency at all. Unique for India's CA market.
- **ICAI statutory prompts**: Pre-built CARO 2020, SA 700 prompts are genuinely useful.
- **SHA-256 tamper verification**: Cryptographic hash on exported reports is a strong differentiator.
- **Offline RAG**: Local FAISS + Ollama is sophisticated and privacy-preserving.

### What Would Stop Users from Adopting It
1. **Hardcoded CA firm name in every report** — a CA cannot ship reports branded as "M/S SHARMA & ASSOCIATES."
2. **Broken PDF export** (`self.client_combo` AttributeError) — users cannot export anything.
3. **No multi-firm support** — a single firm name for all reports is incompatible with CA network practices.
4. **No actual GSTIN verification** — the rule engine checks format but cannot verify against the GSTN portal (offline limitation, but users expect real verification).
5. **Ollama is a non-trivial setup** — CA firms don't have DevOps staff. A simpler fallback UI is needed.

### Features That Are Missing
1. CA firm profile settings (name, membership no., FRN)
2. Password reset flow beyond "contact sysadmin"
3. Real notification system (upcoming deadlines from DB)
4. Dark mode (button exists but does nothing)
5. Global search functionality
6. Multi-firm / multi-user access control UI
7. GSTIN portal verification (even if offline fallback)
8. Materiality calculation wizard
9. Report versioning / draft vs final
10. Email/WhatsApp export (encrypted PDF attachment)

### Features That Are Unnecessary
- `FinancialYear` table — this level of normalization is overkill for a single-firm tool; a string `financial_year` suffices.
- `AuditTeam` model — team management is defined in DB schema but has zero UI.
- `RiskProcedureLink` model — defined but never queried in any UI.
- The "Air-Gapped Local Mode" link in login — it opens a message box explaining what offline means. Remove.

---

## 12. Feature Recommendations

### 50 High-Impact Feature Ideas (Ranked by ROI)

| # | Feature | ROI |
|---|---|---|
| 1 | CA firm settings (name, FRN, membership no.) | 🔴 Blocker |
| 2 | Real PDF export fix (remove `self.client_combo` bug) | 🔴 Blocker |
| 3 | Password reset via CLI with OTP-style hash | 🔴 High |
| 4 | Real notification system from DB (deadlines) | 🔴 High |
| 5 | Global search (clients, documents, findings) | 🟠 High |
| 6 | Dark mode implementation | 🟠 High |
| 7 | UDIN validation with regex before export | 🟠 High |
| 8 | Ollama status check on AI panel open | 🟠 High |
| 9 | Show actual logged-in user name/role in sidebar | 🟠 High |
| 10 | Lazy loading of dashboard pages | 🟠 High |
| 11 | Materiality calculator wizard (SA 320) | 🟠 High |
| 12 | Audit engagement workflow status tracker | 🟠 High |
| 13 | Bulk client import from CSV/Excel | 🟡 Medium |
| 14 | Document multi-select and batch upload | 🟡 Medium |
| 15 | Report version history (draft v1, v2, final) | 🟡 Medium |
| 16 | Engagement timeline / Gantt view | 🟡 Medium |
| 17 | PDF digital signature with actual DSC (pkcs12) | 🟡 Medium |
| 18 | Export working papers to Word (.docx) | 🟡 Medium |
| 19 | Chat history persistence across sessions | 🟡 Medium |
| 20 | AI model selector (llama3, mistral, gemma) | 🟡 Medium |
| 21 | Trial balance auto-mapping to Schedule III | 🟡 Medium |
| 22 | Benford's Law visualization chart | 🟡 Medium |
| 23 | Client portal (read-only web view of report) | 🟡 Medium |
| 24 | Backup encryption with master password | 🟡 Medium |
| 25 | GST 2B reconciliation import | 🟡 Medium |
| 26 | Income tax 26AS fetch and reconcile | 🟡 Medium |
| 27 | Form 3CD clause-by-clause checklist | 🟡 Medium |
| 28 | SA 315 risk identification matrix | 🟡 Medium |
| 29 | Confirmation dialogs on all destructive actions | 🟡 Medium |
| 30 | Keyboard focus ring styles | 🟡 Medium |
| 31 | In-app changelog/update notes | 🟢 Low |
| 32 | Multi-language support (Hindi, Gujarati) | 🟢 Low |
| 33 | Custom rule creation UI | 🟢 Low |
| 34 | Audit file export to ZIP | 🟢 Low |
| 35 | Engagement letter template generator | 🟢 Low |
| 36 | Peer review assignment workflow | 🟢 Low |
| 37 | Physical inventory count sheet | 🟢 Low |
| 38 | KMP (directors) auto-population from MCA | 🟢 Low |
| 39 | Debtors/Creditors age analysis | 🟢 Low |
| 40 | Statutory due date calendar | 🟢 Low |
| 41 | Bank reconciliation worksheet | 🟢 Low |
| 42 | Related party transaction flagging | 🟢 Low |
| 43 | Fixed asset register import | 🟢 Low |
| 44 | Net worth certificate generator | 🟢 Low |
| 45 | Audit opinion tracker (unmodified/qualified/adverse) | 🟢 Low |
| 46 | Biometric login via Windows Hello | 🟢 Low |
| 47 | Scheduled auto-backup to network drive | 🟢 Low |
| 48 | Print preview for working papers | 🟢 Low |
| 49 | Offline GSTIN format + checksum validation | 🟢 Low |
| 50 | E-mail encrypted PDF to client | 🟢 Low |

### 25 UX Improvements
1. Remove pre-filled credentials from login screen
2. Remove role selector from login (derive from DB)
3. Add first-run onboarding wizard (add firm, add first client, upload first doc)
4. Add "scroll to bottom" button in AI chat
5. Add clear chat history button
6. Show actual time-based greeting ("Good Morning / Afternoon / Evening")
7. Add loading spinners to all DB operations
8. Add confirmation dialogs on delete operations
9. Persist last active page across sessions
10. Add breadcrumb navigation ("Dashboard > Clients > ABC Corp")
11. Add keyboard shortcut cheat sheet overlay (Ctrl+/)
12. Functional global search with fuzzy matching
13. Real Ollama connection status indicator (green/red dot)
14. "What's New" tooltip on fresh installs
15. Add progress indicator during document ingestion
16. Collapse sidebar on small screens
17. Add "Recently Viewed" section to dashboard
18. Toast notifications instead of QMessageBox for non-critical info
19. Add table column sorting to all QTableView instances
20. Add "Export to Excel" option on findings and clients lists
21. Engagement switching should show a confirmation modal
22. Add keyboard shortcut for logout (Ctrl+Shift+Q)
23. Show last sync/refresh time on dashboard
24. Empty state improvements: add action buttons (e.g., "Add First Client")
25. Add PDF preview before export

### 25 UI Improvements
1. Implement real dark mode with QSS dark theme
2. Define a color constants module (`theme.py`)
3. Replace emoji icons with proper SVG icon set (Phosphor or Lucide)
4. Add focus ring styles (`QPushButton:focus { outline: 2px solid #0ea5e9; }`)
5. Consistent button sizing (all primary buttons same height: 36px)
6. Fix search bar to be functional or remove it
7. Display logged-in user name and role in sidebar
8. Add status badges to sidebar items (e.g., "3" badge on Risk Analysis)
9. Implement toast notification system (bottom-right slide-in)
10. Fix chart to show real months (current FY)
11. Add chart tooltips (hover to see data values)
12. Improve table row hover states
13. Add column-level sorting indicators to table headers
14. Add date picker widget to due date fields (replace plain `QLineEdit`)
15. Standardize all form labels to use `objectName` QSS selectors
16. Improve empty state widgets with colored icons and CTA buttons
17. Add animated progress indicator for OCR/LLM operations
18. Right-click context menu on table rows (View, Edit, Delete)
19. Add page title breadcrumb to every screen header
20. Use `QSplitter` for resizable panels in AI Analysis view
21. Fix typography: define 5 text size tokens and use consistently
22. Add tooltips to all action buttons
23. Fix notification popup to show real data
24. Add "Copy to Clipboard" on SHA-256 hash in reports
25. Consistent card border-radius across all pages (use 12px everywhere)

### 25 Performance Improvements
1. Defer all `__init__` DB queries to `showEvent()` or `QTimer.singleShot(0)`
2. Fix SQLite `mmap_size` to 256 MB (not 30 GB)
3. Lazy-load pages on first navigation (not all on startup)
4. Fix N+1 in `populate_client_selector()` with a JOIN
5. Cache `ClientRepository.get_all()` with a 5s TTL
6. Only refresh dashboard data when navigating TO dashboard (not on every nav)
7. Limit chat bubble count to 50; discard oldest on overflow
8. Paginate the working papers and findings lists (show 20 at a time)
9. Use `session.query(...).options(selectinload(...))` for eager loading
10. Add `expire_on_commit=False` to `SessionLocal` to prevent DetachedInstanceError
11. Add `QThreadPool` with max 4 threads instead of spawning unlimited `QThread`s
12. Compress FAISS index storage (use `IndexIVFFlat` instead of `IndexFlatIP` for >10k docs)
13. Pre-warm SentenceTransformer model on background thread at startup
14. OCR: process pages in parallel with `multiprocessing.Pool` instead of sequential
15. Batch `session.bulk_insert_mappings` for document page saves
16. Add `QAbstractTableModel.dataChanged` signal on partial updates instead of full reset
17. Cache `AuditProjectsTableModel._client_cache` across refreshes (not rebuild every time)
18. Use `QTimer` for dashboard metric refresh (every 30s) instead of on-nav-click
19. Compress rule engine results before saving to DB (JSON → msgpack)
20. Stream Ollama response without building a full string buffer first
21. Add `PRAGMA optimize` to SQLite on app close
22. Use `memory_profiler` to baseline memory on 100+ document sessions
23. Profile startup time with `cProfile` and target <2s cold start
24. Pre-render report HTML template once; only interpolate variables on change
25. Add DB connection pool min/max settings for multi-thread workers

### 25 Security Improvements
1. Remove hardcoded default credentials from login screen
2. Force password change on first login (add `must_change_password` column)
3. Fix `logout()` to call `auth_manager.revoke_session(token_str)`
4. Fix RBAC check: `if not sm.current_session or not sm.check_permission(...)`
5. Add login attempt counter with exponential backoff
6. Lock account after 10 failed attempts (add `failed_login_count` column)
7. Validate UDIN format with regex before export
8. Add PBKDF2 upgrade path: rehash on next login automatically (already in code — ensure it runs)
9. Redact password field on every app start (not just on echo mode toggle)
10. Store `user_id` not `user_email` in session JWT-style claims
11. Add integrity check on `.active_sessions.dat` before decryption
12. Log all RBAC denials to audit trail (already in code — verify it fires)
13. Add `PRAGMA secure_delete=ON` to SQLite to overwrite deleted rows
14. Encrypt `file_path` references in `Document` table (reveal via decryption)
15. Add 2FA option (TOTP via `pyotp`) for Partner-level accounts
16. Use `secrets.compare_digest` on UDIN comparison (already on passwords, extend)
17. Sanitize all text before HTML injection in report templates (f-string into HTML is XSS-risky in QTextDocument)
18. Add session inactivity timer that triggers auto-logout (UI-level, not just token expiry)
19. Secure `DigitalSignatureManager` hash with HMAC rather than plain SHA-256
20. Use `os.urandom` for `AESCryptoEngine` nonce (verify current implementation)
21. Add file type allowlist for document uploads (only PDF, XLSX, CSV)
22. Check uploaded file size limit before OCR (prevent 1 GB PDF OOM)
23. Redact email from `SessionToken.to_dict()` serialization
24. Add `audit_log` entry on every report export with full metadata
25. Run `bandit` static security scan and fix all HIGH findings

### 25 Developer Experience Improvements
1. Add `pre-commit` hooks with `ruff`, `black`, `bandit`
2. Add type annotations to all function signatures (only ~30% covered currently)
3. Create `CONTRIBUTING.md` with setup instructions
4. Add `mypy` strict mode configuration to `pyproject.toml`
5. Add `pytest-qt` for UI widget testing
6. Add integration test for full login → create client → upload doc flow
7. Add Makefile with `make dev`, `make test`, `make build`
8. Add `requirements.txt` pin hashes (`pip-compile --generate-hashes`)
9. Add `CHANGELOG.md` with semantic versioning
10. Define `PlaceholderWidget` or remove the reference (critical NameError)
11. Add docstrings to all public methods in services layer
12. Move hardcoded strings to `constants.py` (ICAI report templates, firm name, etc.)
13. Add `conftest.py` with shared fixtures (in-memory SQLite, mock session)
14. Add coverage requirement enforcement (≥80%) in CI
15. Set up GitHub Actions for `pytest` on push
16. Add `docker-compose.yml` for development environment with Ollama
17. Create `scripts/seed_demo_data.py` for reproducible demo environment
18. Move database PRAGMA constants to `config.py`
19. Add environment variable documentation to `README.md`
20. Use `logging.getLogger(__name__)` consistently (most files do; some miss)
21. Add `__all__` to all `__init__.py` files
22. Replace bare `except Exception` with typed exceptions throughout
23. Add `@property` type hints to SQLAlchemy model properties
24. Create shared `conftest.py` fixture for `QApplication` (currently duplicated across test files)
25. Add `scripts/check_health.py` that validates DB, Ollama, and FAISS status

---

## 13. Refactoring Roadmap

### 🔴 Critical (Do Immediately)

| Item | Effort | Risk | Benefit |
|---|---|---|---|
| Fix `self.client_combo` AttributeError in `export_pdf()` | 30 min | None | Unblocks all PDF exports |
| Fix `PlaceholderWidget` NameError in dashboard | 30 min | None | Prevents app crash on page load errors |
| Remove hardcoded CA firm name from reports | 2h | Low | Makes product usable for real CAs |
| Remove pre-filled `admin123` password from login UI | 30 min | None | Basic security hygiene |
| Fix RBAC bypass: `if sm.current_session and not sm.check_permission()` | 1h | Low | Closes auth bypass on session expiry |
| Fix `logout()` to revoke session token | 1h | Low | Prevents session reuse after logout |

### 🟠 High Priority

| Item | Effort | Risk | Benefit |
|---|---|---|---|
| CA firm settings screen (name, FRN, membership no.) | 1 day | Low | Core product functionality |
| Defer all DB queries in `__init__` to `showEvent()` | 1 day | Medium | Startup performance |
| Lazy load stacked pages on first visit | 0.5 day | Low | Startup performance |
| Fix N+1 in `populate_client_selector()` | 2h | Low | Query performance |
| Add login rate limiting (3 attempts → backoff) | 0.5 day | Low | Security |
| Merge `AuditProject` into `Engagement` | 3 days | High | Schema consistency |
| Functional global search | 2 days | Medium | Core UX feature |
| Pass authenticated user to `DashboardWindow` | 1h | Low | Show real user info |
| Implement dark mode QSS theme | 1 day | Low | UI feature users expect |

### 🟡 Medium Priority

| Item | Effort | Risk | Benefit |
|---|---|---|---|
| UDIN validation with regex | 2h | None | Regulatory compliance |
| Define `theme.py` color constants | 0.5 day | Low | Design system consistency |
| Replace emoji icons with SVG library | 2 days | Low | Accessibility + consistency |
| Add accessible names to all widgets | 1 day | Low | WCAG compliance |
| Toast notification system | 1 day | Low | UX improvement |
| Ollama connection status badge | 2h | Low | User trust |
| First-run onboarding wizard | 2 days | Low | Adoption |
| Add `expire_on_commit=False` to session | 1h | Low | Prevent DetachedInstanceError |
| Fix SQLite `mmap_size` to 256 MB | 15 min | None | Correctness |
| Limit chat history to 50 messages | 2h | Low | Memory |
| Fix audit progress chart months | 2h | Low | Data accuracy |

### 🟢 Nice to Have

| Item | Effort | Risk | Benefit |
|---|---|---|---|
| TOTP 2FA for Partner accounts | 3 days | Medium | Security upgrade |
| Export to Word (.docx) | 2 days | Low | User convenience |
| Trial balance auto Schedule III mapping | 3 days | Medium | Core automation |
| Report versioning (draft/final) | 2 days | Medium | Professional workflow |
| Engagement letter template generator | 2 days | Low | Value-add feature |
| CI/CD GitHub Actions setup | 1 day | Low | Developer experience |

---

## 14. Technical Debt Report

| Issue | Severity | File(s) | Impact | Est. Effort | Fix |
|---|---|---|---|---|---|
| `self.client_combo` undefined in `export_pdf()` | 🔴 BLOCKER | `reports.py:215` | 100% export failure | 30 min | Replace with `client_name` variable |
| `PlaceholderWidget` NameError | 🔴 BLOCKER | `dashboard.py:801` | App crash on page failure | 30 min | Import or define `PlaceholderWidget` |
| Hardcoded CA firm credentials in reports | 🔴 Critical | `reports.py:160-162` | Unusable for any real CA | 2h | Load from Settings |
| Pre-filled `admin123` password in UI | 🔴 Critical | `login.py:119,126` | Security liability | 30 min | Remove `setText()` calls |
| RBAC bypass on null session | 🔴 Critical | `dashboard.py:879` | Auth bypass | 1h | Fix condition logic |
| `logout()` doesn't revoke session | 🟠 High | `auth_service.py:73-75` | Session persistence after logout | 1h | Call `revoke_session()` |
| DB queries in widget `__init__` | 🟠 High | `dashboard.py:705-765`, `ai_analysis.py:145` | UI blocking on startup | 1 day | Defer to `showEvent()` |
| `AuditProject` vs `Engagement` duality | 🟠 High | `models.py:104-139` | Data inconsistency | 3 days | Schema consolidation |
| N+1 in `populate_client_selector()` | 🟠 High | `dashboard.py:903-914` | Scales poorly | 2h | JOIN query |
| `mmap_size=30_000_000_000` SQLite pragma | 🟠 High | `database.py:48` | OOM risk on low-RAM machines | 15 min | Set to 268435456 |
| `refresh_realtime_data()` on every nav | 🟡 Medium | `dashboard.py:849` | Unnecessary DB load | 1h | Only refresh on Dashboard tab |
| Chat bubble memory leak | 🟡 Medium | `ai_analysis.py:307` | Memory growth in long sessions | 2h | Cap at 50 messages |
| Hardcoded months in chart | 🟡 Medium | `dashboard.py:370` | Wrong data display | 2h | Use real calendar months |
| Hardcoded notification alerts | 🟡 Medium | `dashboard.py:978-986` | Misleads users | 2h | Query DB for real alerts |
| OCR confidence default `98.5` | 🟡 Medium | `models.py:177` | Fabricated metric | 2h | Default to `null`, set only after OCR |
| No `setTabOrder()` anywhere | 🟡 Medium | All UI files | Accessibility | 1 day | Define tab chains per dialog |
| No accessible names on widgets | 🟡 Medium | All UI files | Screen reader incompatible | 1 day | `setAccessibleName()` per widget |
| Bare `except Exception` swallowing errors | 🟡 Medium | `reports.py:143`, others | Silent failures | 2h | Log + show user feedback |
| UDIN no validation | 🟡 Medium | `reports.py:87` | Invalid UDIN on official docs | 2h | Add regex validator |
| `datetime.utcnow()` deprecated (Python 3.12+) | 🟡 Medium | `models.py`, `auth.py`, multiple | DeprecationWarning | 1h | Use `datetime.now(UTC)` |
| Role selector on login screen misleads | 🟡 Medium | `login.py:133-134` | UX confusion + fake RBAC | 30 min | Remove combo, use DB role |
| `c.name`, `l` single-letter variables | 🟢 Low | `ai_analysis.py`, `dashboard.py` | Readability | 0.5 day | Rename variables |
| No `__all__` in `__init__.py` | 🟢 Low | All packages | Import pollution | 0.5 day | Define explicit exports |

---

## 15. Final Scorecard

| Category | Score | Rationale |
|---|---|---|
| **Architecture** | 6/10 | Solid 3-layer pattern (UI → Service → Repo) but the `AuditProject`/`Engagement` duality and session-not-propagated issues are architectural debt. The refactored dashboard helpers are clean. |
| **Code Quality** | 5/10 | Good Pydantic config, good PBKDF2 implementation, good QThread workers. But hardcoded credentials, fake default values, single-letter variables, bare except clauses, and fabricated OCR confidence bring the score down. |
| **Maintainability** | 6/10 | 51/51 tests passing is excellent. `dashboard.py` at 990 LOC is borderline. The services layer is clean where used. Inline `setStyleSheet()` everywhere will be painful to restyle. |
| **Performance** | 4/10 | DB queries on main thread during `__init__`, all 12 pages loaded at startup, N+1 queries, 30GB SQLite mmap, uncontrolled chat bubble accumulation. These are not theoretical — they will be felt on first use. |
| **Security** | 6/10 | PBKDF2 at 600k iterations is excellent. AES-256-GCM session persistence is correct. BUT: hardcoded `admin123`, RBAC bypass on null session, logout not revoking token, no login rate limiting — these are real vulnerabilities. |
| **Accessibility** | 2/10 | No `setTabOrder()`, no `setAccessibleName()`, color-only risk indicators, contrast failures on subtitles, no focus rings. The app is effectively keyboard-inaccessible and screen-reader blind. |
| **UI Design** | 6/10 | The design language is coherent and modern (Slate palette, Sky primary, good card layouts). The QTableView with custom delegate is premium. But broken search, fake notifications, hardcoded firm name, and unused dark mode button undermine trust. |
| **UX Design** | 5/10 | The 3-column AI copilot layout is excellent. The ICAI prompt library is genuinely useful. But pre-filled credentials, non-functional search, silent engagement auto-creation, no onboarding, and no real notifications create a frustrating experience. |
| **Scalability** | 5/10 | SQLite WAL mode handles concurrent reads well. But N+1 queries, lazy loading absence, and no pagination mean the app will degrade noticeably at 50+ clients and 500+ documents. |
| **Developer Experience** | 6/10 | 51 tests, pytest setup, pyproject.toml config, clean repo structure, and good docstrings on security modules. Missing: CI, type annotations on most functions, `mypy`, `pre-commit`, `CHANGELOG.md`. |
| **Product Readiness** | 4/10 | The product **cannot currently export a PDF** due to the `self.client_combo` bug. It cannot be branded with any CA's actual firm name. The default password is displayed in the UI. These are launch blockers. |

### **Overall Score: 5.1 / 10**

> **Summary**: FinAuditPro has a genuinely sophisticated core — offline RAG, PBKDF2 auth, AES-256 sessions, immutable audit ledger, and a well-structured services layer. The architecture, when followed, is correct. The test suite is commendable. However, the product has two crash-level bugs (`self.client_combo`, `PlaceholderWidget`), hardcoded credentials displayed in the UI, an unofficial CA firm name on every legal document, and an accessibility score that makes it unusable for keyboard/screen-reader users. Before any CA firm can actually use this software for a real engagement, the six critical items in the roadmap must be resolved. The bones are good; the surface needs significant work.
