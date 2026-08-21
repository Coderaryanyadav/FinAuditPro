# FinAuditPro — Milestone 3 Handoff Prompt (Financial Data Import & Deterministic Analytics)

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestone 1 (Firm→Client→Engagement→Dashboard) and Milestone 2 (Documents & OCR) are merged,
> tested, and the app launches. If either is incomplete, finish it first — do not build analytics
> on an unfinished foundation.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1 (Firm → Client → Engagement → Dashboard) and 2 (document upload → validate → hash → store → extract/OCR → classify → index → view → search → link-as-evidence) are complete. **Milestone 3 is financial-data import and deterministic analytics.**

The master brief is explicit and you must obey it here: **build deterministic analytics BEFORE relying on any AI.** No LLM is used in this milestone. Everything you build must be exact, explainable, reproducible, and testable. And the hard rule of the whole product still binds: **no fake functionality** — no fabricated numbers, no anomaly results that aren't computed from real rows, no dashboard figure that isn't derived from a real query.

Everything from earlier milestones still binds: clean layer boundaries; UI touches no ORM/session; **money is never a `float`** (integer paise or `Decimal`); fail-closed RBAC in the service layer; a hash-chained audit event for every mutation; datasets are scoped to exactly one engagement and analytics can never cross engagement/client boundaries.

## 0. Ground truth: environment (verified — but re-verify in your sandbox before relying on it)

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access** (build only with installed packages), reference code in gitignored `_reference/`.

**Verified facts that shape this milestone:**

- **`pandas` 3.0.3, `numpy` 2.5.1, `openpyxl` 3.1.5, `python-dateutil` 2.9** are installed. Use pandas/openpyxl only as the **file-reading and tabular-wrangling layer at the infrastructure edge** — never let a pandas DataFrame leak into the domain or UI layers. Note pandas 3.0 defaults to copy-on-write; write code that doesn't depend on in-place mutation of slices.
- **`Decimal` (stdlib `decimal`) is your money type.** pandas reads numeric cells as `float64` by default, which **silently loses precision** on money. → Read money columns as **strings** (`dtype=str` / `converters=`), strip Indian digit grouping (`1,23,456.78`), and parse to `Decimal`, then into the Milestone-1 `Money` value object (integer paise). A cell you cannot parse to an exact amount is a **row error**, not a `0.0`.
- **Real sample datasets already exist** at `_reference/tests/sample_data/` — use them as fixtures (copy the ones you need into `tests/fixtures/`; `_reference/` is gitignored so don't depend on it at runtime). Verified real columns:
  - **Trial Balance** (`AuditPro_Input_Client_Trial_Balance_Sample_V1.0_04Jan2026.xlsx`): `Account Code, Account Name, Type, Opening Dr, Opening Cr, Debit, Credit, Closing Dr, Closing Cr`
  - **General Ledger** (`AuditPro_Input_General_Ledger_Extract_Sample_V1.0_04Jan2026.xlsx`): `Date, Voucher Type, Voucher No, Account Code, Account, Debit, Credit, Narration, Reference, Created By`
  - **Bank Statement** (`AuditPro_Input_Bank_Statement_Sample_V1.0_04Jan2026.xlsx`): `Date, Txn ID, Description, Debit, Credit, Balance, Value Date, Reference`
  - **Vendor Master** (`AuditPro_Input_Vendor_Master_Data_Sample_V1.0_04Jan2026.xlsx`): `Vendor Code, Vendor Name, PAN, GSTIN, Address, Contact, Phone, Email, Terms, Credit Limit, Status`
  - Shorter variants also exist (`Sample_General_Ledger.xlsx`, `Sample_Bank_Statement.xlsx`, `Sample_Vendor_Master.xlsx`).
- **SQLite 3.53.4** (from Milestone 1). Large ledgers can be many thousands of rows — index the transaction tables and paginate; never load a whole dataset into the UI at once (see §6).
- **Formula-injection escaping** is required on any XLSX/CSV **export** (prefix cells beginning with `= + - @ tab CR` with `'`). Import is read-only, but remember this for the export path.

## 1. Scope of Milestone 3 — one complete vertical, top to bottom

**Import a dataset → detect & map columns → validate & normalize (original preserved) → persist typed rows → run deterministic analytics → present exceptions → promote an exception to a structured Finding with traceable evidence.**

Cover these dataset types (start with Trial Balance + General Ledger fully, then Bank Statement; the others can be a thinner pass this milestone): **Trial Balance, General Ledger, Journal Entries, Bank Statement, Sales Register, Purchase Register.** Fixed-asset register and expense register are later.

**Out of scope this milestone:** any AI/LLM, embeddings/RAG, and the full GST reconciliation module (GSTIN *format+checksum* validation already exists from Milestone 1 — reuse it; don't rebuild it). Stay in the import-and-deterministic-analytics lane and make it genuinely correct.

## 2. Import pipeline — an explicit, inspectable, reproducible flow

Mirror the document pipeline's discipline: named stages, persisted status, real errors, audit events. **Never silently modify imported data — the original dataset is immutable; normalization produces a separate, derived representation, and every transformation is recorded.**

1. **Ingest.** User picks an XLSX/CSV and declares (or you infer) the dataset type. Store the raw file the same way documents are stored (content-hashed, original preserved, provenance kept). A dataset is linked to exactly one engagement.
2. **Detect columns.** Read the header row; **auto-map source columns to the canonical fields** for the declared dataset type using name heuristics (e.g. `Debit`→debit, `Voucher No`/`Vch No`→voucher_number, `Txn ID`→transaction_id, `Account Code`→account_code). Return each mapping **with a confidence and the reason**. Auto-detection is a suggestion, never the final word.
3. **Column-mapping UI (mandatory).** The auditor sees the detected mapping and can **remap any column**, mark columns ignored, and set the header row / sheet. **Persist the mapping** so the exact same import is reproducible and re-runnable. When auto-detection fails, the auditor maps manually — that path must work, not just the happy path.
4. **Validate & normalize per row.**
   - **Dates** → parse (dateutil, day-first for Indian formats `DD-MM-YYYY` / `DD/MM/YYYY`) to real dates; an unparseable date is a **row error**.
   - **Amounts** → strings → `Decimal` → `Money` (see §0); reject float. Handle blank vs zero distinctly (blank ≠ 0).
   - **Identifiers** (PAN/GSTIN in vendor master) → reuse the Milestone-1 value objects; format/checksum issues are **warnings on that row**, surfaced, not silent.
   - Every row that fails validation is collected into a **row-level error report** (row number, column, raw value, reason) shown to the auditor. Import is **all-or-nothing per your choice** — decide and record in `DECISIONS.md` whether bad rows block the import or are quarantined alongside a clean load; either way nothing is silently dropped or coerced.
5. **Persist typed rows.** Normalized rows go into typed tables (see §3), each carrying a back-reference to its **source row number in the original file** — this is the evidence anchor. Keep the raw imported values too (so the auditor can always see "what the file said" vs "what we parsed").
6. **Audit.** Import start, mapping chosen, validation summary (n rows ok / n errors), completion — all hash-chained audit events.

## 3. Data model additions (new numbered migration on the existing DB)

Normalized, one source of truth each, all engagement-scoped:
- `datasets` — id, engagement_id FK, dataset_type enum, source filename, content sha256, stored path, imported_by FK, status, row counts (total/ok/error), the **persisted column mapping** (JSON), timestamps.
- `ledger_entries` (General Ledger / Journal) — id, dataset_id FK, source_row_no, date, voucher_type, voucher_number, account_code, account_name, **debit_paise (int)**, **credit_paise (int)**, narration, reference, created_by_raw, raw_values JSON. Indexed on (dataset_id, account_code), (dataset_id, date), (dataset_id, voucher_number).
- `trial_balance_lines` — id, dataset_id FK, source_row_no, account_code, account_name, type, opening_dr_paise, opening_cr_paise, debit_paise, credit_paise, closing_dr_paise, closing_cr_paise.
- `bank_transactions` — id, dataset_id FK, source_row_no, date, value_date, txn_id, description, debit_paise, credit_paise, balance_paise, reference.
- Sales/Purchase register tables analogously (date, party, invoice no, taxable, tax, total — all paise).
- `analysis_runs` — id, dataset_id FK, analytic_id, analytic_version, parameters JSON, run_by FK, run_at, summary counts. (Reproducibility: same dataset + same analytic version + same params ⇒ same result.)
- `exceptions` (the deterministic-analytics output) — id, analysis_run_id FK, dataset_id FK, analytic_id, **severity/indicator level** (not "fraud"), title, description, the **exact rows implicated** (list of source_row_no / entry ids), the **computed evidence** (e.g. "sum of debits 12,34,567.00 ≠ sum of credits 12,34,566.00; difference ₹1.00"), status (open / under-review / accepted / dismissed), reviewer, timestamps. An exception is a structured object, never a formatted string.
- **Evidence + Findings bridge.** Reuse the Milestone-2 `evidence_links`. When an auditor **accepts an exception**, it is promoted to a structured **Finding** (create the `findings` table now if Milestone 1/2 didn't: id, engagement_id, title, description, category, severity, amount_paise, affected_account, source [`deterministic_analytic` here], `ai_generated=false`, status, preparer, reviewer, timestamps) that links back through evidence to the exact dataset rows. This closes the traceability loop: **Finding → analytic → dataset rows → original file.**

## 4. The deterministic analytics — exact, explainable, versioned

Build these as a **versioned, independently testable analytics registry** (same philosophy as the compliance rules: each analytic has an id, a version, a title, a plain-language explanation, and parameters with sensible **configurable** defaults — no magic numbers buried in code). Each analytic takes typed rows and returns structured `exceptions` with the implicated rows and the computed numeric evidence. **Deterministic: same input ⇒ same output**; if any sampling is used, it must be seeded.

**Foundational integrity checks (do these first — they're the bread-and-butter of an audit):**
- **Trial balance balances**: total debits == total credits (and opening/closing consistency). Report the exact imbalance amount. This is the canonical first check.
- **GL ↔ TB agreement**: sum of ledger movements per account reconciles to the trial balance movement for that account; flag accounts that don't tie.
- **Bank running-balance continuity**: each row's balance == previous balance + credit − debit; flag breaks.

**Transaction anomaly indicators (from the master brief — present ALL as "exception / anomaly / indicator / requires review", NEVER as fraud or proof):**
- **Duplicates** — define the match key explicitly and make it configurable (e.g. same date + amount + account, or same voucher number reused). Show the duplicate group.
- **Unusually large amounts** — statistical outliers (e.g. z-score / IQR over the account or dataset); report the threshold and the value. It's an *indicator*, with its statistical basis shown.
- **Round-number amounts** — define "round" explicitly (e.g. exact multiples of ₹1,000/₹10,000 or N trailing zeros); configurable threshold.
- **Weekend postings** — transactions dated on Sat/Sun. **Do NOT hardcode an Indian public-holiday list** (holidays are year- and state-specific and change) — weekend detection is safe from the date alone; "holiday" postings should only be offered if the auditor supplies/loads a holiday calendar, treated as versioned user data, not baked-in facts.
- **Sequential-number gaps** — gaps/duplicates in voucher/invoice number sequences (the GL has `Voucher No`); report the missing ranges.
- **Negative balances / unexpected sign** — e.g. a credit balance in an asset account.
- **Concentration** — large share of a total in few accounts/parties/days.
- **Benford's-law first-digit deviation** — a classic audit *indicator* for further review; present the observed vs expected distribution and the deviation, explicitly labelled as an indicator requiring judgement, not a conclusion.

**Financial analytics (comparative, for planning/substantive review):**
- Period/account **movement**, **variance analysis** (absolute + %), **trend** across periods where multiple datasets exist, **ratio analysis** (only ratios computable from the imported data — don't invent inputs), **ageing** (receivables/payables buckets: 0–30/31–60/61–90/90+) where a register with dates supports it.

Every analytic result carries: what was checked, the parameters used, the rows implicated, the exact computed figures, and a plain explanation. Vocabulary is enforced: **exception, anomaly, indicator, requires review** — a lint/test that greps the analytics + UI strings for "fraud"/"fraudulent" and fails is a nice touch.

## 5. Off-thread execution & performance

Large ledgers are slow to import and analyze. Run **import parsing and analytics on a worker** (reuse the Milestone-2 background-job mechanism), with real progress (rows processed / analytics completed) and retryable failures — **never a fake progress bar, never a frozen UI.** Push aggregation into SQL where sensible rather than pulling every row into Python. Paginate all row views.

## 6. UI (professional, dense, keyboard-first — consistent with earlier milestones)

- **Import wizard**: pick file → choose/confirm dataset type → **review & edit the column mapping** (with detected confidence) → see the validation/error summary → confirm import.
- **Dataset views**: paginated, sortable, filterable tables of the typed rows, with the raw-vs-parsed values visible; strong empty/loading/error states.
- **Analytics view**: pick a dataset, run analytics (off-thread), see the exceptions list grouped by analytic and severity/indicator level; drill into an exception to see the exact implicated rows and computed evidence; **accept** (→ promotes to a Finding with evidence links) or **dismiss** (with a reason, audited).
- Every number on screen is derived from a real query/computation. If there's no data, show a real empty state — never a decorative zero.

## 7. Acceptance criteria for Milestone 3

1. New numbered migration applies cleanly on the existing DB and is idempotent to re-run.
2. Importing the **real sample Trial Balance** parses all money columns to exact `Decimal`/paise (no float), and the **trial-balance-balances** analytic reports the true debit/credit totals and any imbalance — verified against the actual fixture.
3. Importing the **real sample General Ledger** persists typed `ledger_entries` with correct debit/credit paise and dates, each carrying its source row number.
4. **Column remapping works**: change a mapping in the UI, re-import, and the persisted mapping reproduces the exact same result.
5. A file with **bad rows** (unparseable date, malformed amount) produces a **row-level error report** (row/column/value/reason) — nothing is silently coerced to zero or dropped.
6. At least these analytics are real and unit-tested against fixtures with **known expected outputs**: trial-balance-balances, GL↔TB agreement, duplicate detection, large-amount outliers, round-number, weekend postings, sequential-number gaps.
7. **Determinism test**: running an analytic twice on the same dataset yields identical exceptions.
8. **Engagement isolation test**: analytics/queries on Engagement A never surface Engagement B's dataset rows.
9. **Accepting an exception** creates a structured `Finding` (with `ai_generated=false`) linked via evidence back to the exact dataset rows and the original file; **dismissing** records an audited reason. No "fraud" language anywhere (add the grep test).
10. Import + analytics run **off the UI thread** with real progress; the UI never blocks (manually verified). `tests/test_architecture.py` still passes (no pandas/ORM in domain or UI; no module > ~400 lines); the app launches and the full **import → map → validate → analyze → accept-as-finding** flow is manually exercised and reported honestly.

Then stop and report before the next milestone (Risk & Materiality, then AI).

## 8. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification; if something was skipped or unrunnable (lint/mypy aren't installable here), say so plainly.** Update `BUILD_PROGRESS.md` and `DECISIONS.md` (record: bad-rows-block vs quarantine; duplicate match-key default; outlier method + thresholds; why weekend-only and no hardcoded holidays; money-parsing approach). Absolutely no fabricated figures, no anomaly results not computed from real rows, no dead buttons, no TODOs masquerading as implementation. If a piece can't be done properly with the installed tooling, leave it out and say why.

**Begin the financial-data import and deterministic analytics subsystem.**
