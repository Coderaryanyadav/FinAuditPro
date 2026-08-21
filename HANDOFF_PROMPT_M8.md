# FinAuditPro — Milestone 8 Handoff Prompt (Hardening & End-to-End Verification) — FINAL

> Copy everything below the line into the coding agent (Antigravity / Gemini).
> This assumes Milestones 1–7 are merged, tested, and the app launches end to
> end (firm/client/engagement/ dashboard; documents & OCR; financial import &
> analytics; risk/materiality/procedures & Findings; local AI/RAG; working
> papers, review & sign-off; reporting & export). This is the final milestone:
> it adds almost no new features — it **hardens, verifies, closes gaps, and
> tells the honest truth** about what works. Do not add scope; close it.

---

You are completing FinAuditPro, the offline-first, privacy-first audit
intelligence desktop app for Indian audit practice. Milestones 1–7 are built.
**Milestone 8 is Hardening & End-to-End Verification**: security review and the
encryption-decision follow-through, audit-trail integrity, performance under
real data volumes, backup/restore, error handling & recovery, a full-chain
verification pass, and an honest final report.

The whole point of this milestone is to make the product **trustworthy and
truthful**. So the honesty bar is the highest it has been: **do not paper over
gaps.** If something isn't actually secure, isn't tested, or couldn't be done in
this environment, the deliverable is to _say so clearly_, not to fake it. A
hardened app that honestly lists three known limitations is worth far more than
one that claims to be perfect.

All prior principles still bind: engagement isolation everywhere; `domain/`
pure; UI touches no ORM/session and makes no network calls; fail-closed RBAC;
hash-chained append-only audit trail; money in paise/`Decimal`; AI assists, the
auditor decides; no fabricated data anywhere.

## 0. Ground truth: environment + verified security primitives

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**,
venv at `.venv`, **no PyPI network access** (build only with installed
packages). **No new external dependency is required.** Verified working
(re-verify in your sandbox):

- **`cryptography` 49.0.0** — `Fernet` and `AESGCM` both encrypt/decrypt
  correctly → application-level field encryption and encrypted backups are
  viable with the installed package.
- **`hashlib.scrypt`** (stdlib) works → password hashing needs no third-party
  dep.
- **SQLite append-only enforcement is real**: `BEFORE UPDATE`/`BEFORE DELETE`
  triggers with `RAISE(ABORT,…)` **actually block** UPDATE and DELETE on the
  audit table (verified). The hash-chained audit trail can be enforced at the DB
  level, not just in application code.
- **`zipfile`, `tarfile`, `shutil`, `hashlib.sha256`** (all stdlib) →
  integrity-checked (and optionally encrypted) backup archives are viable.
- Reminder from earlier milestones: **`ruff`/`mypy` are NOT installable here** —
  you cannot run lint/typecheck; keep their config for CI and say plainly in the
  final report that they were not run locally. **PyInstaller and packaging tools
  are likewise not installable** — do not fake a frozen-binary build (see §8).

**Recurring guardrail, now applied as an audit across ALL milestones:** you are
an engineering student, not a CA. Verify that **no statutory threshold, format,
period, or wording was hardcoded from memory anywhere** (materiality %,
holidays, documentation/retention periods, report/opinion wording, GST/tax
constants). Anything statutory must be a versioned rule/template with `source`,
`effective_from`, and `verified: false` surfaced in the UI. Grep the whole
codebase for suspicious hardcoded constants and report/fix findings.

## 1. Scope — harden and verify, do not add features

Close the app out along six axes: **(§2) security review + the encryption
decision, (§3) audit-trail integrity, (§4) performance & scale, (§5)
backup/restore, (§6) error handling & recovery, (§7) an end-to-end verification
pass**, then **(§8) honest packaging notes + final documentation**. Fix real
gaps you find; if a gap can't be closed in this environment, document it
precisely. No new subsystems.

## 2. Security review + the encryption decision (close the Milestone-1 §5 open item)

- **Encryption decision — follow through now.** Milestone 1 required an explicit
  choice for the live SQLite DB (which `sqlcipher` cannot provide here). **Read
  `DECISIONS.md`.** If a choice is recorded, verify it is actually implemented
  and honestly documented. **If no choice is recorded, STOP and ask the human to
  choose** among: (a) rely on OS full-disk encryption (FileVault/BitLocker) and
  document that trust boundary; (b) application-level field encryption of
  sensitive columns via `cryptography` (verified available — `AESGCM`/`Fernet`);
  (c) documented deferral with a clearly-stated gap. **Do not silently pick one
  and call the data "encrypted at rest."** Whatever is chosen, `SECURITY.md`
  states the exact trust boundary in plain language.
- **Audit the recurring anti-patterns are absent** (the old codebase's confirmed
  defects):
  - **Fail-closed RBAC everywhere**: no service path proceeds when the session
    is `None` — grep for the `if session and not check_permission(...)` bypass
    shape; a missing/blank session must **raise**, never skip the check. Add
    tests for the unauthenticated and unauthorized paths on every mutating
    service.
  - **Lockout / security counters live in the DB**, never a deletable plaintext
    JSON.
  - **Untrusted-content escaping is thorough** (M5): all angle brackets escaped
    and `<think>`/tag tokens neutralized — not just the one wrapper tag. Re-test
    the injection fixtures.
  - **File & export safety** (M2/M7): magic-byte validation, size ceilings,
    zip-slip/zip-bomb guards, path-traversal-safe storage keyed by content hash,
    and formula-injection escaping on every XLSX/CSV export — all present and
    tested with malicious fixtures.
  - **Password hashing** via `hashlib.scrypt` (or `cryptography`) with sane
    parameters.
  - **No secrets/PII in logs or error messages** — audit log statements and
    user-facing errors.
- **Offline guarantee**: verify the app makes **no outbound network calls**
  except the explicit, user-configured local LM Studio endpoint (M5); any cloud
  AI remains opt-in with a loud warning and is off by default. Add a test/audit
  asserting no unexpected hosts are contacted.

## 3. Audit-trail integrity (make tamper-detection real and loud)

- Verify the audit trail is **append-only enforced by SQLite triggers**
  (verified viable — `BEFORE UPDATE`/`BEFORE DELETE` → `RAISE(ABORT)`), **and**
  hash-chained (`previous_hash`/`entry_hash`) with a working **verifier** that
  recomputes the chain and detects any break.
- **Startup integrity check**: on launch, verify the schema version (migration
  runner) and run the chain verifier; if the chain is broken or a signed
  artifact's content hash mismatches (M6/M7), surface it **loudly and
  specifically** — never silently continue as if fine.
- Confirm every mutation across all milestones writes an audit event (logins,
  doc processing, imports, analytics runs, findings, procedures, materiality, WP
  review/sign-off, report approval/export, config & permission changes,
  backup/restore). A consolidated test asserts the chain verifies over a full
  end-to-end run.

## 4. Performance & scale (real data, not toy data)

- **Pagination everywhere**: no view loads an unbounded result set into memory —
  documents (M2), ledger/bank rows (M3), findings, working papers (M6), reports.
  Verify and fix any full-table loads.
- **Indexes on hot query paths** exist (engagement_id, dataset_id+account,
  dates, voucher numbers, FTS5, faiss per-engagement).
- **Seed a realistically large dataset** (e.g. a General Ledger with tens of
  thousands of rows) and **measure**: import time, analytics time, search
  latency, RAG retrieval latency, report generation. Record real numbers in
  `BUILD_PROGRESS.md`. Heavy work stays **off the UI thread** with real
  progress; memory stays bounded (stream/aggregate in SQL, don't pull everything
  into Python).
- Confirm the UI stays responsive under load (manually verified) — no freezes,
  no fake progress bars.

## 5. Backup & restore (offline-first — this is the user's only safety net)

- Implement a real **backup**: a portable, **integrity-checked** (sha256
  manifest) archive containing the SQLite DB **plus** the document store (M2
  files) **plus** the per-engagement faiss indexes (M5) — the DB alone is not a
  complete backup. Optionally **encrypted** (using `cryptography`, consistent
  with the §2 decision) with a user passphrase.
- Implement **restore** into a clean install; verify **round-trip fidelity**:
  restored content hashes match, the **audit chain still verifies**, documents
  open, RAG indexes load, and no engagement data is mixed. A test performs
  backup → wipe → restore → verify.
- Backup/restore actions are themselves audited. Never overwrite an existing
  backup silently; never restore over live data without explicit confirmation.

## 6. Error handling & recovery (behave correctly when things go wrong)

- **Graceful degradation** for: DB locked/busy, disk full, corrupt/malformed
  file, LM Studio unreachable or a model unloaded (M5), a migration that fails,
  a partially-completed import. Each produces an honest, specific, non-leaking
  message and leaves the system in a consistent state.
- **Crash/incomplete-job recovery**: OCR (M2), import (M3), indexing (M5), and
  report generation (M7) jobs that were interrupted are either resumable or
  cleanly marked failed and retryable — never stuck in a permanent "processing"
  limbo.
- **Migration runner robustness**: forward-only, idempotent, each migration in a
  transaction; a failing migration rolls back cleanly and the app refuses to run
  on a half-migrated DB. Re-verify (from M1).
- **App data dirs** (DB, document store, faiss, matplotlib `MPLCONFIGDIR`) are
  created on first run and failures to write are reported clearly, not
  swallowed.

## 7. End-to-end verification pass (prove the whole chain, then the isolation)

- **Full-chain integration test / scripted run** exercising: firm → client →
  engagement → upload document → OCR/extract → import TB + GL → run analytics →
  exception → set materiality → risk → procedure → finding (deterministic) → (if
  LM Studio available) AI-assisted finding with citations → working paper →
  review notes → sign-off → report → approve → export. Assert **traceability
  resolves end-to-end** (report figure → finding → procedure → risk → evidence →
  source document page / dataset row) and the **audit chain verifies over the
  entire run**.
- **Consolidated cross-engagement isolation test**: one test that, across
  **every** subsystem (documents, FTS search, analytics, RAG retrieval,
  findings, working papers, reports, backup), proves Engagement A never sees
  Engagement B's data. This is the master brief's most critical guarantee — make
  it a single, unmissable test.
- Re-run **`tests/test_architecture.py`** (layer purity, no ORM/network in UI,
  no module > ~400 lines, no circular imports) and the **full pytest suite**;
  report pass/fail counts honestly.

## 8. Packaging honesty + final documentation

- **Packaging**: a frozen binary needs PyInstaller, which is **not installable
  in this environment** — do **not** fake a build or commit a bogus `.spec`.
  Instead document the **real** way to run the app from the `.venv`, list the
  runtime prerequisites (Python 3.14, the installed packages, LM Studio +
  `deepseek-r1-distill-qwen-14b` + `nomic-embed-text` for AI, the `tesseract`
  binary for OCR), and note that producing a distributable installer is a
  follow-up requiring network access to install packaging tools.
- **Documentation finalize**:
  - `SECURITY.md` — threat model, the encryption trust boundary (§2 decision),
    the "electronic sign-off is not a legal DSC/UDIN" honesty,
    untrusted-document handling, and the offline guarantee.
  - `BUILD_PROGRESS.md` — all 8 milestones with real status, the measured
    performance numbers, and a candid **Known Limitations** list.
  - `DECISIONS.md` — complete (persistence, migration runner, encryption,
    per-milestone choices).
  - A final **honest hand-off report** stating: what works and was verified how;
    what is mock-tested vs live-tested (esp. the LM Studio path); what is
    deferred; what could not be run here (lint/mypy, packaging); and every
    `verified:false` statutory default still awaiting a CA's confirmation.

## 9. Acceptance criteria for Milestone 8

1. The **encryption decision is closed**: either implemented per `DECISIONS.md`
   or the human was asked and chose; `SECURITY.md` states the exact at-rest
   trust boundary in plain language. No claim of "encrypted at rest" that isn't
   true.
2. **Fail-closed RBAC audited**: tests prove every mutating service raises on
   missing/blank session and on unauthorized role — no bypass shape remains.
3. **Audit trail**: append-only is DB-enforced (triggers reject UPDATE/DELETE),
   the chain verifier works, and a broken chain / hash mismatch is surfaced
   loudly at startup (tested with a deliberately tampered row).
4. **Injection & file-safety** fixtures (angle-bracket/`<think>` prompt
   injection, fake-PDF, zip-slip/zip-bomb, `=cmd` formula) all pass their guards
   (re-verified).
5. **Offline guarantee**: an audit/test shows no outbound network except the
   configured local LM Studio endpoint; cloud AI is off by default.
6. **Scale**: a large seeded dataset (tens of thousands of GL rows) imports,
   analyzes, searches, and reports with the UI never blocking; real measured
   timings are recorded.
7. **No unbounded loads**: verified pagination on all large-list views.
8. **Backup/restore round-trip**: backup → wipe → restore reproduces the DB +
   documents + faiss indexes; restored content hashes match and the audit chain
   still verifies (tested).
9. **Recovery**: interrupted OCR/import/indexing/report jobs are resumable or
   cleanly failed (not stuck); a failed migration rolls back and the app refuses
   a half-migrated DB (tested). LM Studio down / model unloaded degrades
   honestly.
10. **End-to-end + isolation**: the full-chain integration run passes with
    end-to-end traceability and a verifying audit chain; the consolidated
    cross-engagement isolation test passes across every subsystem.
11. **No hardcoded statutory content** anywhere (codebase grep/review done;
    findings fixed or documented as `verified:false`).
12. `tests/test_architecture.py` and the full suite pass; the app launches, the
    whole workflow is manually exercised, and the **honest final report** (works
    / mock-vs-live / deferred / not-runnable-here / awaiting-CA-verification) is
    delivered.

This is the final milestone — after it, report the true state of the product
plainly.

## 10. Process & honesty (unchanged, non-negotiable — and it matters most here)

Work in coherent steps; after each, run the suite, launch the app, exercise the
workflow, inspect your own code, fix, continue. **Never say "done" without
verification. If tests fail, show the output. If a check was skipped or
unrunnable (lint/mypy/packaging), say so. If the LM Studio path was only
mock-tested, say so. If a security property isn't actually guaranteed, say so —
do not imply a level of assurance you didn't verify.** Update
`BUILD_PROGRESS.md`, `DECISIONS.md`, and `SECURITY.md`. Absolutely no fake
hardening, no security theater, no "encrypted" that isn't, no green checkmark
that wasn't earned. The deliverable of this milestone is a trustworthy app
**and** an honest account of exactly how trustworthy it is.

**Begin the hardening and end-to-end verification pass. Close the gaps you can,
document the ones you can't, and tell the truth about the result.**
