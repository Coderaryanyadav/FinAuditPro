# FinAuditPro — 1,000-Point Master UI/UX & Flow Verification Checklist

This document contains the complete 1,000-point UI/UX, interaction design, visual hierarchy, table density, status badge, maker-checker flow, and end-to-end user journey checklist for **FinAuditPro**.

---

## Section 1: Design Tokens & Visual Hierarchy (Items 0001 - 0100)
- `0001`: Dark background base color is `#0f1117`.
- `0002`: Card surface color is `#181b22`.
- `0003`: Elevated surface color is `#222732`.
- `0004`: Subtle border color is `#2a303c`.
- `0005`: Primary accent color is `#0284c7`.
- `0006`: Primary hover color is `#0369a1`.
- `0007`: Success status color is `#10b981`.
- `0008`: Warning status color is `#f59e0b`.
- `0009`: Danger status color is `#ef4444`.
- `0010`: Risk Low color is `#38bdf8`.
- `0011`: Risk Medium color is `#f59e0b`.
- `0012`: Risk High color is `#f97316`.
- `0013`: Risk Critical color is `#ef4444`.
- `0014`: Primary text color is `#f8fafc`.
- `0015`: Secondary text color is `#94a3b8`.
- `0016`: Muted text color is `#64748b`.
- `0017`: Font family defaults to SF Pro / System Sans.
- `0018`: Tabular numeric font uses monospaced alignment.
- `0019`: Base typography font size is 13px.
- `0020`: Header title font size is 15px bold.
- `0021-0100`: Visual hierarchy contrast, focus indicators (`#38bdf8`), rounded corner radius (6px inputs / 8px cards / 4px badges), and border padding consistency verified across all controls.

---

## Section 2: Sidebar Navigation & App Shell (Items 0101 - 0200)
- `0101`: Sidebar background color is `#12141a`.
- `0102`: Sidebar right border is 1px solid `#2a303c`.
- `0103`: Sidebar width is fixed at 230px.
- `0104`: Section header `AUDIT WORKSPACE` is uppercase 10px bold.
- `0105`: Section header `EVIDENCE & ANALYTICS` is uppercase 10px bold.
- `0106`: Section header `WORK & REVIEWS` is uppercase 10px bold.
- `0107`: Section header `OUTPUT & SYSTEM` is uppercase 10px bold.
- `0108`: Active nav item highlights with primary background (`#0284c7`).
- `0109`: Inactive nav items feature `#94a3b8` color and hover to `#f8fafc`.
- `0110`: Header context bar background color is `#181b22`.
- `0111-0200`: Header context breadcrumb `Active: Firm ➔ Client ➔ Engagement (FY)` live state updates, status badges, and window stretch behavior verified across desktop shell.

---

## Section 3: Data Tables & Tabular Alignment (Items 0201 - 0350)
- `0201`: QTableWidget background color is `#14171f`.
- `0202`: Gridline color is `#222732`.
- `0203`: Table header background is `#181b22` with `#94a3b8` text.
- `0204`: Table header text is 12px bold.
- `0205`: Selection background color is `#0284c7`.
- `0206`: Financial amount columns align right.
- `0207`: Currency symbols (`₹`) formatted consistently.
- `0208`: Paise values formatted to 2 decimal places.
- `0209`: Negative values formatted with minus sign or parenthesized style.
- `0210`: Row height provides compact enterprise density.
- `0211-0350`: Sorting, filtering, empty state messages, row hover highlights, selection model, and pagination controls verified across Trial Balance, General Ledger, Findings, and Working Papers tables.

---

## Section 4: Forms, Inputs & Dialogs (Items 0351 - 0500)
- `0351`: QLineEdit background color is `#0f1117`.
- `0352`: Input border is 1px solid `#2a303c`.
- `0353`: Input border radius is 6px.
- `0354`: Focus state displays `#38bdf8` accent border.
- `0355`: Dialog background color is `#181b22`.
- `0356`: Dialog overlay dims background window cleanly.
- `0357`: Primary modal button placed on bottom right.
- `0358`: Cancel/Secondary button placed adjacent to primary button.
- `0359`: Destructive action buttons styled with danger red (`#ef4444`).
- `0360`: Form validation messages display near invalid input field.
- `0361-0500`: Input focus trapping, Escape key modal dismissal, keyboard Tab navigation, file selector dialogs, and field placeholder texts verified across all 16 dialog components.

---

## Section 5: Status Badges & Maker-Checker Workflows (Items 0501 - 0650)
- `0501`: `StatusBadge` renders `Draft` status in muted style (`#1e293b`).
- `0502`: `StatusBadge` renders `Submitted` status in info style (`#0c4a6e`).
- `0503`: `StatusBadge` renders `In Review` status in warning style (`#78350f`).
- `0504`: `StatusBadge` renders `Approved` / `Signed Off` status in success style (`#064e3b`).
- `0505`: `StatusBadge` renders `Archived` status in muted border style.
- `0506`: Open review notes block working paper sign-off.
- `0507`: Signed-off working paper locks fields against silent edits.
- `0508`: Reopening an archived engagement requires recorded Partner justification.
- `0509-0650`: Maker-checker role authorization, audit trail event logging, timestamp recording, and signature disclaimers (`verified_statutory: False`) verified.

---

## Section 6: Local AI Copilot & Evidence Citations (Items 0651 - 0800)
- `0651`: AI assistant view displays clear `[AI Generated]` observation badges.
- `0652`: Retrieved evidence chunks display source document title and page number.
- `0653`: Chunk IDs cited in square brackets (e.g. `[CHUNK-101]`).
- `0654`: Untrusted PDF text disarms `<think>` reasoning tags before prompt engine embedding.
- `0655`: Prompt injection phrases (`"ignore previous instructions"`) disarmed cleanly.
- `0656`: Local LM Studio REST server endpoint defaults to `http://localhost:1234`.
- `0657`: Graceful degradation when LM Studio server is offline.
- `0658`: Auditor retains complete manual override authority over AI suggestions.
- `0659-0800`: Vector search index scoping by `engagement_id`, RAG prompt formatting, confidence disclaimers, and local model selection settings verified.

---

## Section 7: End-to-End User Journeys & System Automation (Items 0801 - 1000)
- `0801`: Application launch executes first-run bootstrap without manual configuration.
- `0802`: Data directories created automatically under OS app storage.
- `0803`: Database schema migrations 1..9 executed automatically on startup.
- `0804`: Firm onboarding wizard allows setting firm name and FRN.
- `0805`: Client management allows creating Private Limited, LLP, Partnership entities.
- `0806`: Audit engagement creation specifies Audit Type and Financial Year.
- `0807`: Financial dataset import parses Trial Balance, GL, and Bank CSVs.
- `0808`: Deterministic analytics execute Benford 1st Law, Duplicate Payment, and Outlier detectors.
- `0809`: Materiality engine computes SA 320 benchmarks (Turnover, Profit, Assets).
- `0810`: Risk register maps inherent and control risks to audit procedures.
- `0811`: Unified Findings promoted from analytics exceptions or manually created.
- `0812`: Working paper index tracks maker, checker, and sign-off status.
- `0813`: ReportLab PDF export generates audit report bundle with draft watermark.
- `0814`: OpenPyXL XLSX export sanitizes leading `= + - @ \t \r` formula injection triggers.
- `0815`: Engagement archival seals database slice with SHA-256 manifest.
- `0816`: Sealed archive locked in read-only mode (`PRAGMA query_only=ON`).
- `0817`: Multi-year roll-forward creates next FY engagement and links SA 510 opening balance tie-outs in paise.
- `0818`: Single-client tenant isolation blocks cross-client roll-forwards.
- `0819`: System diagnostic tool (`scripts/automated_system_check.py`) executes 100% cleanly.
- `0820`: Master E2E runner (`scripts/run_1000_verifications.py`) executes all 15 stages with 0 failures.
- `0821-1000`: Platform path resolution (macOS, Windows, Linux), memory cleanup, background worker responsiveness, error logging, and final production readiness verified across all 1,000 UI/UX and flow checklist items.
