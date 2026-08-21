# FinAuditPro — Milestone 7 Handoff Prompt (Reporting & Export)

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestones 1–6 are merged, tested, and the app launches (firm/client/engagement/dashboard;
> documents & OCR; financial import & analytics; risk/materiality/procedures & Findings; local
> AI/RAG; working papers, review & sign-off). If any is incomplete, finish it first — a report is
> an assembly of everything below it, and it must draw only on real, reviewed data.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1–6 are complete. **Milestone 7 is Reporting & Export** — assembling the engagement's real, auditor-reviewed outputs (findings, exceptions, analytics, risk register, materiality, working-paper index) into structured, auditor-reviewed reports, and exporting data safely to PDF / XLSX / CSV.

The product principles still govern, and two of them are sharper than ever here: **no fake functionality** (every number in a report comes from a real query — never a plausible-looking figure), and **AI assists, the auditor decides** (the app never authors a statutory opinion; a generated report is a *draft* the auditor reviews and approves). Everything is engagement-scoped; a hash-chained audit event is written for every mutation; fail-closed RBAC in the service layer; `domain/` stays pure; UI touches no ORM/session.

## 0. Ground truth: environment + the THREE hard constraints for this milestone

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access**. **Verified installed and working (re-verify in your sandbox):**
- **`reportlab` 5.0.0** — verified it renders real PDF bytes (output starts with `%PDF`). This is your primary PDF engine for structured documents.
- **`openpyxl` 3.1.5** for XLSX, **`csv`** (stdlib) for CSV. **`pypdf` 6.14.2** for merging/metadata/page counts.
- **`matplotlib` 3.11.1** for real charts (render to PNG/SVG and embed). Note: matplotlib needs a **writable config dir** — set `MPLCONFIGDIR` to an app data path, and use the non-interactive `Agg` backend (no GUI backend).
- **Qt alternative**: `QPdfWriter` + `QTextDocument` are importable (PySide6 6.11.1) — a viable HTML→PDF path for richly-formatted docs if you prefer it over reportlab. Pick one primary path, note it in `DECISIONS.md`.
- **No new external dependency is required.**

**Hard constraint #1 — the app NEVER authors statutory report content from memory** (this milestone's version of the recurring "don't hardcode law" rule, and the most important one here):

> You are an engineering student, not a CA. The **statutory auditor's report (the opinion), CARO clauses, Companies Act / SA 700-series formats, and any prescribed wording** are legally-governed and change. **You must not generate, hardcode, or paraphrase statutory opinion wording from memory.** Such formats exist in this app **only as auditor-supplied, versioned templates** carrying `source`, `effective_from`, `jurisdiction`, and a `verified: false` flag surfaced in the UI — the auditor provides/reviews the actual wording. The app **assembles and manages** documents and fills in real data; it does **not** decide or author the opinion. Internal, firm-defined deliverables (findings report, management letter, exceptions summary, engagement summary) are safer to generate — but they are still drafts the auditor reviews, and any statutory text within them is template-driven, not invented.

**Hard constraint #2 — spreadsheet/CSV formula-injection escaping is mandatory on every tabular export:**

> Any cell whose value begins with `=`, `+`, `-`, `@`, tab (`\t`), or carriage return (`\r`) must be prefixed with a single quote (`'`) before writing to XLSX/CSV, because a client name, narration, or finding title is attacker-influenced data (e.g. a vendor named `=cmd|'/c calc'!A1`). This applies to **every** export path. It is an acceptance-criterion with a malicious-fixture test.

**Hard constraint #3 — a generated report is a DRAFT until approved, and any sign-off on it is not a legal signature** (carry Milestone 6's honesty):

> Drafts are watermarked "DRAFT — not for issuance." Approval uses the Milestone-6 maker–checker discipline. Any signature/attestation on a report is an **internal workflow attestation + tamper-evident record**, **not** an IT Act 2000 DSC or an ICAI UDIN. If a UDIN field exists, the auditor enters it; the app never generates or validates it as authoritative. Never imply legal effect.

## 1. Scope of Milestone 7 — one coherent vertical, top to bottom

**Pick a versioned template → select scope (which findings/sections/date range) → assemble the report from real queries → preview (real data, click-through to evidence) → generate → review & approve → export to PDF and XLSX/CSV (injection-safe) → store the output as a hashed, immutable, audited artifact.**

Build the **findings / engagement report** fully as the primary deliverable, plus **safe data exports** (findings, exceptions from M3, trial balance / analytics results, risk register) to XLSX/CSV. Support the *mechanism* for statutory-report templates (auditor-supplied), but do **not** ship hardcoded statutory wording.

**Out of scope this milestone:** authoring statutory opinions (mechanism only, per #1), engagement archival/retention enforcement (M8/hardening), emailing or uploading reports anywhere (offline-first — export to disk only), and any new AI.

## 2. Report templates — versioned, sourced, editable (not hardcoded statutory text)

- Templates load from **versioned data files** (same philosophy as the compliance-rules engine): id, name, report type (`findings_report`, `management_letter`, `exceptions_summary`, `engagement_summary`, or an auditor-imported statutory format), version, `source`, `jurisdiction` (nullable), `effective_from`, `verified: false`, and a **section structure** (ordered sections, each declaring what real data it pulls — e.g. "accepted findings by severity", "trial-balance summary", "working-paper index & sign-off status").
- Templates are **editable/importable** by the firm. Default templates ship clearly marked `verified: false`. No section contains prescribed statutory wording baked into code.

## 3. Report assembly — every figure is a real query, reproducible, with provenance

- Assemble content **only from real queries** against the engagement: accepted **findings** (M4 deterministic + M5 AI-assisted, human-accepted — with their AI badge/citations preserved), **exceptions** (M3), **analytics summaries** (M3), **risk register & materiality** (M4), **working-paper index & sign-off status** (M6). If a section has no data, it says so honestly — never a decorative zero or a filler paragraph.
- **Provenance & reproducibility**: each report records template id+version, engagement, a **data as-of / snapshot reference**, generated-by, timestamp, and a **content hash of the assembled content model**. Assembling from the same snapshot + template version yields the same content model (deterministic assembly; hash the normalized content model, not the PDF bytes, since PDF metadata/timestamps vary). Regeneration creates a new **version**; prior versions are retained.
- **Traceability**: every finding/figure in the report links back through `evidence_links` to its **source document page (M2) / dataset row (M3)**. A test asserts the report's contents resolve to real underlying records.

## 4. Export & rendering — real files, injection-safe, real charts

- **PDF** via reportlab (primary) or Qt `QPdfWriter`+`QTextDocument` — produce a real, openable PDF. Draft PDFs carry the "DRAFT — not for issuance" watermark until approved.
- **XLSX** via openpyxl, **CSV** via stdlib `csv` — with **formula-injection escaping on every cell** (#2), tested.
- **Charts**: matplotlib with the `Agg` backend and a writable `MPLCONFIGDIR`, rendered from **real data** (e.g. findings-by-severity, exception counts, ageing buckets) and embedded — never a stock/placeholder image.
- No client data in logs or error messages; outputs written only to the engagement's managed storage on local disk.

## 5. Review/approve workflow + storage as a hashed artifact

- A report moves `Draft → Under Review → Approved/Final → Superseded` (reuse the Milestone-6 state-machine + maker–checker discipline; illegal transitions rejected and audited). Approval requires an authorized role (fail-closed RBAC); the approver and timestamp are recorded, with the #3 "not a legal signature" notice shown and persisted.
- The generated PDF/XLSX is **stored as a content-hashed, immutable artifact in the Milestone-2 document system** (with `source='generated'`), so it lives in the document store, is searchable/auditable, and preserves provenance. Regenerating supersedes but never destroys the prior version.

## 6. Data model additions (new numbered migration on the existing DB)

Engagement-scoped, normalized: `report_templates` (versioned, sourced, `verified:false`, section structure JSON — or load templates from data files with a registry table), `reports` (id, engagement_id, template id+version, title, type, status enum, data as-of, content model JSON/reference, content hash, generated_by, reviewed_by, approved_by, timestamps), `report_artifacts` (id, report_id, format [pdf|xlsx|csv], stored document id/path, content hash), and reuse `evidence_links` / the M2 `documents` store for the rendered outputs. Every mutation (template imported, report generated, reviewed, approved, superseded, exported) writes a **hash-chained audit event**. Migration applies cleanly on an existing M1–M6 DB and is idempotent.

## 7. UI (professional, dense, keyboard-first — consistent with earlier milestones)

- **Reports list** per engagement: type, status, version, generated/approved by & when, format(s) available; filter/sort; strong empty/loading/error states.
- **Generate-report wizard**: pick template → select scope (findings/sections/date range) → **preview the assembled content with real data** and click-through to evidence (reuse M2 viewer / M3 rows) → generate → review → approve → export PDF/XLSX/CSV.
- Draft watermark visible in preview and PDF; approved report shows the approver + the "not a legal DSC/UDIN" notice; superseded versions are retained and viewable.
- Generation/export runs **off the UI thread** with real progress; never a fake bar, never a frozen UI.

## 8. Acceptance criteria for Milestone 7

1. New numbered migration applies cleanly on an existing M1–M6 DB and is idempotent.
2. A **findings/engagement report assembles only real data** from real queries (accepted findings, exceptions, analytics, WP index); a test asserts the figures match the underlying records — no fabricated numbers, honest empty sections.
3. **Formula-injection escaping**: a test exports data containing malicious values (`=`, `+`, `-`, `@`, tab, CR — e.g. a finding titled `=cmd|...`) to XLSX and CSV and asserts each is prefixed with `'`.
4. **PDF export** produces a real, openable file (`%PDF`), and a draft carries the "DRAFT — not for issuance" watermark (verified).
5. **No hardcoded statutory content**: statutory formats/opinion wording exist only as auditor-supplied, versioned, sourced, `verified:false` templates; the app authors no opinion from memory (reviewed and documented; default templates clearly unverified).
6. **Provenance & reproducibility**: a report records template version, data as-of, generated-by, timestamp, and a content hash; regenerating from the same snapshot yields the same content model; regeneration versions it and retains prior versions (tested).
7. **Traceability test**: a finding/figure in the report resolves via `evidence_links` to its source document page / dataset row; M5 AI-assisted findings retain their AI badge + citations in the report.
8. **Review/approve + storage**: the report status workflow reuses M6 (illegal transitions rejected & audited); approval is RBAC-gated (fail-closed) and shows the "not a legal signature" notice; the rendered output is stored as a content-hashed, immutable artifact in the M2 document store.
9. **Engagement isolation**: a report for Engagement A never pulls Engagement B's data (tested); no client data written to shared logs.
10. Generation/export runs **off the UI thread** with real progress; `tests/test_architecture.py` still passes (assembly logic testable, no ORM in UI, no module > ~400 lines); the app launches and the full **pick template → assemble → preview → generate → review → approve → export (injection-safe PDF/XLSX/CSV)** flow is manually exercised and reported honestly.

Then stop and report before the final milestone (hardening — security review, performance/pagination under large data, backup/restore, encryption decision follow-through, error handling & recovery, and an end-to-end verification pass across all milestones).

## 9. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification; if something was skipped or unrunnable (lint/mypy aren't installable here), say so plainly.** Update `BUILD_PROGRESS.md` and `DECISIONS.md` (record: PDF engine choice reportlab-vs-Qt; template data-file format and its unverified defaults + sources; deterministic-assembly/content-hash approach; formula-injection escaping rule; that the app never authors statutory opinions and that report sign-off is not a legal DSC/UDIN). Absolutely no fabricated figures, no placeholder charts, no statutory wording invented from memory, no dead buttons, no TODOs masquerading as implementation. If a piece can't be done properly, leave it out and say why.

**Begin the reporting & export subsystem. Every number is real and traceable; statutory wording is the auditor's, not yours; every export is injection-safe; a report is a draft until a human approves it.**
