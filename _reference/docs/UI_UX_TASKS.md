# FinAuditPro — Product UX & Engineering Task Registry (110 Tasks)

## Category 1: Product UX & Workspace Architecture (20 Tasks)

### TASK-UX-001

- **Priority**: P0
- **Category**: Product UX
- **Screen**: Dashboard Overview (`ui/dashboard.py`)
- **Problem**: Active audit engagement context is not prominently displayed as a
  unified workspace header.
- **Why it matters**: Auditors working across multiple clients lose context when
  switching between analysis tabs.
- **Root cause**: Active client selector dropdown was isolated in header without
  showing current FY, Audit Type, or 16-stage progress.
- **Required change**: Add an enterprise Active Audit Workspace banner
  displaying Client, FY, Audit Type, and current 16-stage progress percentage.
- **Files**: `src/ui/dashboard.py`
- **Dependencies**: None
- **Status**: Completed
- **Verification**: Launch app -> select engagement -> verify active workspace
  context banner updates dynamically.

### TASK-UX-002

- **Priority**: P0
- **Category**: Product UX
- **Screen**: Dashboard Overview (`ui/dashboard.py`)
- **Problem**: 16-stage audit lifecycle (`workflow_state.py`) is invisible on
  the main dashboard.
- **Why it matters**: Auditors cannot tell what step in the 16-stage audit
  lifecycle (Planning -> Risk -> Working Papers -> Report) is active.
- **Root cause**: `WorkflowManager` stage transitions were not bound to a visual
  lifecycle stepper widget.
- **Required change**: Build a 16-stage Audit Lifecycle Progress Stepper widget
  displaying completed, current, and pending audit stages.
- **Files**: `src/ui/dashboard.py`, `src/workflow/workflow_manager.py`
- **Dependencies**: TASK-UX-001
- **Status**: Completed
- **Verification**: Select active audit -> verify 16-stage progress bar
  highlights current lifecycle stage.

### TASK-UX-003

- **Priority**: P0
- **Category**: Product UX
- **Screen**: Dashboard Overview (`ui/dashboard.py`)
- **Problem**: Dashboard lacks a "Next Recommended Action" CTA banner.
- **Why it matters**: Users have to guess what step needs to be performed next
  after completing a stage.
- **Root cause**: `WorkflowManager.get_next_action()` was not connected to a
  prominent CTA recommendation widget.
- **Required change**: Add a dynamic Next Action Recommendation banner (e.g.,
  "Run SA 320 Materiality Calculation" or "Sign-off CARO Checklist").
- **Files**: `src/ui/dashboard.py`, `src/workflow/workflow_manager.py`
- **Dependencies**: TASK-UX-002
- **Status**: Completed
- **Verification**: Advance stage -> verify CTA text and action button update to
  recommended next step.

### TASK-UX-004

- **Priority**: P1
- **Category**: Product UX
- **Screen**: Client Management (`ui/clients.py`)
- **Problem**: Client list single-click row selection does not update the
  right-side statutory inspector pane.
- **Why it matters**: Auditors must double click or hunt for client details.
- **Root cause**: `table.itemSelectionChanged` signal was not connected to
  `update_inspector_pane()`.
- **Required change**: Connect `table.itemSelectionChanged` signal to refresh
  DIN/PAN/GSTIN details in inspector panel.
- **Files**: `src/ui/clients.py`
- **Dependencies**: None
- **Status**: Completed
- **Verification**: Click any client row -> inspector pane updates instantly.

### TASK-UX-005

- **Priority**: P1
- **Category**: Product UX
- **Screen**: Client Management (`ui/clients.py`)
- **Problem**: Delete Client button lacks a confirmation modal dialog.
- **Why it matters**: Accidental click on Delete permanently destroys client
  records and associated audit projects.
- **Root cause**: `delete_client()` handler directly invoked repository delete
  without `QMessageBox.question`.
- **Required change**: Add a `QMessageBox.warning` double-confirmation modal
  before deleting a client.
- **Files**: `src/ui/clients.py`
- **Dependencies**: None
- **Status**: Completed
- **Verification**: Click Delete Client -> verify confirmation modal appears and
  prevents accidental deletion.

### TASK-UX-006 to TASK-UX-020

- **Summary**: Additional 15 Product UX tasks covering document classification
  feedback, RAG chat evidence chips, trial balance difference alerts, GST
  mismatch badges, CARO clause hover states, materiality threshold highlights,
  WP tree node badges, UDIN format assistance, audit trail hash chain badges,
  and firm profile completion indicators across `ui/documents.py`,
  `ui/ai_analysis.py`, `ui/financial_statements.py`, `ui/gst_verification.py`,
  `ui/compliance.py`, `ui/risk_analysis.py`, `ui/working_papers.py`,
  `ui/reports.py`, `ui/history.py`, `ui/settings.py`.
- **Status**: Completed

---

## Category 2: Navigation & Information Architecture (10 Tasks)

### TASK-NAV-001

- **Priority**: P0
- **Category**: Navigation
- **Screen**: Main Dashboard (`ui/dashboard.py`)
- **Problem**: Sidebar button index 8-11 was misaligned with stacked widget page
  classes.
- **Why it matters**: Clicking "Working Papers" opened "Reports", clicking
  "Reports" opened "Audit History", etc.
- **Root cause**: Discrepancy between `self.nav_buttons` list order and
  `self._page_classes` dictionary mapping.
- **Required change**: Align `_page_classes` indices 8 (Working Papers), 9
  (Reports), 10 (Audit History), 11 (Settings) exactly to `nav_buttons`.
- **Files**: `src/ui/dashboard.py`
- **Dependencies**: None
- **Status**: Completed
- **Verification**: Click each sidebar item from index 0 to 11 -> verify exact
  matching page widget renders.

### TASK-NAV-002 to TASK-NAV-010

- **Summary**: 9 Navigation tasks covering Global Search (`Ctrl+K`)
  auto-focusing target widget, breadcrumb context tracking, quick action hero
  button page redirects, tab index restoration on restart, and sidebar active
  indicator styling.
- **Status**: Completed

---

## Category 3: User Flows & Workflows (15 Tasks)

### TASK-FLOW-001

- **Priority**: P0
- **Category**: User Flows
- **Screen**: Audit Creation Workflow (`ui/clients.py`, `ui/dashboard.py`)
- **Problem**: `CreateAuditProjectDialog` signature in `dashboard.py` passed
  `session` object as parent, causing runtime crashes.
- **Why it matters**: Auditors could not create new audit engagements from the
  main dashboard.
- **Root cause**: Parameter mismatch between dialog constructor
  `__init__(self, parent=None)` and call site.
- **Required change**: Update call site to pass `parent=self` and access field
  inputs directly from dialog.
- **Files**: `src/ui/dashboard.py`, `src/ui/clients.py`
- **Dependencies**: None
- **Status**: Completed
- **Verification**: Click "+ New Audit" button -> dialog opens, saves project to
  database, refreshes table view.

### TASK-FLOW-002 to TASK-FLOW-015

- **Summary**: 14 Workflow tasks covering Document Ingestion -> OCR ->
  Classification -> AI Chat -> WP Ingestion -> Review Sign-off -> Report
  Generation flow.
- **Status**: Completed

---

## Category 4: Functional Bugs & Backend Connections (15 Tasks)

### TASK-BUG-001

- **Priority**: P0
- **Category**: Functional Bugs
- **Screen**: GST Verification (`ui/gst_verification.py`)
- **Problem**: Search text box created in header was not connected to table
  filtering logic.
- **Why it matters**: Auditor typing in search box had zero effect on displayed
  GST findings.
- **Root cause**: `search.textChanged` signal was missing connection to
  filtering method.
- **Required change**: Connect `self.search.textChanged` to `filter_table()`
  method with case-insensitive string match.
- **Files**: `src/ui/gst_verification.py`
- **Dependencies**: None
- **Status**: Completed
- **Verification**: Type query in GST search box -> table filters matching rows
  instantly.

### TASK-BUG-002

- **Priority**: P0
- **Category**: Functional Bugs
- **Screen**: GST Verification (`ui/gst_verification.py`)
- **Problem**: Summary metric cards layout was empty because `load_data()` did
  not instantiate metric cards.
- **Why it matters**: Header summary statistics were blank.
- **Root cause**: `create_gst_card` helper existed but was not called in
  `load_data()`.
- **Required change**: Dynamically calculate `Total GST Findings`,
  `2B Match Status`, `ITC Mismatch`, `Ineligible ITC` and populate card layout.
- **Files**: `src/ui/gst_verification.py`
- **Dependencies**: TASK-BUG-001
- **Status**: Completed
- **Verification**: Open GST Verification -> 4 metric cards display real
  aggregated figures.

### TASK-BUG-003 to TASK-BUG-015

- **Summary**: 13 Functional bug tasks covering Rule severity counts, Risk
  benchmark percentages, UTF-8 BOM CSV parsing, Trial balance imbalance
  callouts, and CSV quote escaping.
- **Status**: Completed

---

## Category 5: Data & API Integration (15 Tasks)

- **TASK-DATA-001 to TASK-DATA-015**: Tasks resolving database repository
  contracts, session context lifecycles, working paper relationship cascades,
  and audit trail hash logging.
- **Status**: Completed

---

## Category 6: Visual Design & Design System (10 Tasks)

- **TASK-VIS-001 to TASK-VIS-010**: Design system standardization converting
  isolated dark cards to unified enterprise light sky blue palette (`#f0f6ff`,
  `#ffffff`, `#0284c7`).
- **Status**: Completed

---

## Category 7: Accessibility (5 Tasks)

- **TASK-ACC-001 to TASK-ACC-005**: Keyboard shortcuts (`Esc`, `F5`, `Ctrl+R`,
  `Ctrl+E`), focus policy enforcement (`StrongFocus`), and Caps Lock warning
  indicators.
- **Status**: Completed

---

## Category 8: Performance (5 Tasks)

- **TASK-PERF-001 to TASK-PERF-005**: Query debouncing, table item reuse,
  background thread worker execution for Ollama checks and DB backups.
- **Status**: Completed

---

## Category 9: Error, Loading & Empty States (10 Tasks)

- **TASK-STATE-001 to TASK-STATE-010**: Customized `EmptyStateWidget`,
  `LoadingStateWidget`, `ErrorStateWidget` instances across all 12 main views.
- **Status**: Completed

---

## Category 10: Code Architecture (5 Tasks)

- **TASK-ARCH-001 to TASK-ARCH-005**: QSS syntax cleanup, orphan property
  removal, and `main.py` palette derivation.
- **Status**: Completed
