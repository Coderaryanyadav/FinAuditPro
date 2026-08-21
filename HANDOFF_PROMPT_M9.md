# FinAuditPro — Milestone 9 Handoff Prompt (Engagement Archival, Freeze & Retention)

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestones 1–8 are merged, tested, and the app launches end to end (foundation; documents & OCR;
> financial import & analytics; risk/materiality/procedures & Findings; local AI/RAG; working papers,
> review & sign-off; reporting & export; hardening & end-to-end verification). This milestone was
> deliberately deferred out of M6/M7/M8 — it is the **close of the audit lifecycle**: plan → execute
> → document → report → **archive the file**. If anything below it is incomplete, finish that first.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1–8 are complete. **Milestone 9 is Engagement Archival, Freeze & Retention** — finalising a completed engagement into a **frozen, tamper-evident, integrity-sealed audit file**, making it read-only, recording its assembly and retention timelines, allowing read-only historical browsing and a complete audit-file export, and permitting only a permissioned, audited reopen.

This milestone is **deterministic — no new AI is used here** (archived AI-assisted findings keep their M5 badges/citations). Every prior principle still binds: engagement isolation is absolute; `domain/` stays pure; UI touches no ORM/session and makes no network calls; fail-closed RBAC in the service layer; money in paise/`Decimal`; a hash-chained audit event for every mutation; **no fake functionality** and **never say "done" without verification**.

## 0. Ground truth: environment + the TWO hard constraints for this milestone

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access** (build only with installed packages). **No new external dependency is required.** Verified working (re-verify in your sandbox):
- **SQLite 3.53.4 immutability is real, two ways**: opening the DB read-only via URI (`sqlite3.connect("file:…?mode=ro", uri=True)`) blocks writes (`OperationalError`), **and** `PRAGMA query_only=ON` blocks writes on a normal connection (`OperationalError`). Either can enforce "an archived engagement is read-only" at the DB layer, not just in the UI.
- **`PRAGMA integrity_check`** returns `ok` — use it to validate a DB before and after sealing.
- **`zipfile`, `tarfile`, `shutil`, `hashlib.sha256`** (stdlib) build the integrity-checked archive; **`cryptography` 49.0.0** (`AESGCM`/`Fernet`, verified in M8) provides optional passphrase encryption of the archive.
- The M1 hash-chained append-only audit trail (SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers → `RAISE(ABORT)`, verified in M8) must be **preserved intact** through archival and re-verifiable from the archive.

**Hard constraint #1 — the assembly period and retention period are configurable, sourced, `verified:false` content, NOT hardcoded law** (this milestone's version of the recurring rule):

> You are an engineering student, not a CA. The **final-assembly period** (the window after the report date within which the audit file is assembled/finalised) and the **retention period** are governed by auditing standards (e.g. **SA 230 Audit Documentation**) and ICAI/firm policy, and they change. **Do not hardcode a number of days or years as if it were law.** These are **configurable, versioned entries carrying `source`, `effective_from`, and a `verified:false` flag surfaced in the UI**, defaulting to clearly-unverified values the firm edits. The app computes deadlines from the auditor's config and **surfaces** them — it never treats a baked-in period as authoritative.

**Hard constraint #2 — "sealed/frozen" means tamper-evident, NOT legally certified** (carry the M6/M7 honesty):

> Freezing an engagement is an internal **records-management control plus a tamper-evident integrity seal** (content hashes), not a legal attestation, not an IT Act 2000 DSC, not an ICAI UDIN. Say so plainly in the UI and `DECISIONS.md`. **And never auto-delete an audit file:** at end of retention the app *surfaces* the date for the auditor to act — it must not destroy or purge audit documentation on its own.

## 1. Scope of Milestone 9 — one coherent vertical, top to bottom

**Run a pre-archive readiness check → freeze the engagement (lock every writable subsystem) → seal it into an integrity-checked, optionally-encrypted archive with a manifest + content hash → the engagement becomes read-only across the whole app → record assembly/retention timelines → browse the archived engagement read-only and export the complete audit file → permissioned, audited reopen.**

**Out of scope this milestone:** automatic deletion/purging at end of retention (compute and surface the date; never delete — per #2); multi-year roll-forward / carrying data into next year's engagement (next milestone); any new AI.

## 2. Freeze & lock — extend M6 locking to the whole engagement

- A **pre-archive readiness check** computes, from real queries, whether the file is consistent: working papers signed off (M6), reports approved or explicitly excluded (M7), findings resolved/accepted or explicitly carried (M4), **no open review notes** (M6), migrations current, and the audit chain verifies (M8). It reports concrete blockers honestly — never a decorative "ready."
- The auditor may **override** a soft blocker only with a **recorded justification** (audited); hard-invalid states (e.g. a broken audit chain) cannot be sealed.
- **Freezing** sets the engagement status to `Archived` and turns writes **off at the service layer (fail-closed)** and enforces read-only at the **DB layer** (`query_only` / read-only open, verified viable). A write attempt against an archived engagement **raises** — prove it with a test, not just a hidden button.

## 3. The sealed archive — deterministic, integrity-checked, optionally encrypted

- The archive contains the engagement's **complete audit file**: its DB slice (a filtered export of exactly that engagement's rows, with the hash-chained audit trail preserved and re-verifiable), its **documents** (M2 store), its **faiss indexes** (M5), and its **generated reports/artifacts** (M7).
- Build a **sha256 manifest** over every file, plus a **top-level content hash** sealing the whole; assembling the manifest from the same inputs is **deterministic** (sort paths; hash content, not timestamps). Optional **AESGCM/Fernet** passphrase encryption (consistent with the M8 encryption decision).
- The archive is recorded as an artifact and **audited**; never overwrite an existing archive silently.

## 4. Retention & assembly timelines — configurable, sourced, `verified:false`

- Store a versioned **retention config** (assembly-period days, retention-period years, each with `source`, `effective_from`, `verified:false`). From the auditor's config + the report date, compute the **finalisation deadline** and the **retain-until date**, and surface both in the UI with the `verified:false` badge.
- **No auto-deletion.** At/after retain-until, surface a clear prompt for auditor action; the app never purges (#2).

## 5. Read-only historical access + permissioned reopen

- An archived engagement opens in a clearly-marked **read-only mode** across **every** subsystem (documents, findings, working papers, reports, analytics) — immutability enforced at the service/DB layer, tested per subsystem.
- A **reopen/unarchive** is RBAC-gated (fail-closed, e.g. partner-only, configurable), **audited**, requires a recorded **reason**, and **preserves the sealed archive** while creating a new working state (mirror the M6 reopen discipline — never destroy the record of what was sealed).

## 6. Data model additions (new numbered migration on the existing DB)

Engagement-scoped: extend the engagement **status enum** (`Active → Finalizing → Archived → Reopened`); `engagement_archives` (engagement_id, archive path, manifest hash, sealed content hash, encrypted bool, report_date, assembly_deadline, retain_until, sealed_by, timestamp); `retention_config` (versioned, sourced, `verified:false`); `archive_reopen_records` (engagement_id, reopened_by, reason, timestamp, prior archive ref). Reuse the M1 hash-chained audit-event mechanism for **every** mutation (readiness override, freeze, seal, export, reopen). Migration applies cleanly on an existing M1–M8 DB and is idempotent.

## 7. UI (professional, dense, keyboard-first — consistent with earlier milestones)

- **Engagement-close wizard**: readiness check (real blockers listed) → resolve or record an override justification → freeze → seal (optional encryption passphrase) → confirmation showing the sealed content hash.
- **Archived-engagement view**: a prominent read-only/"Archived — sealed on {date}" banner; assembly-deadline and retain-until dates shown with the `verified:false` badge and source; an **Export audit file** action; a permissioned **Reopen** action requiring a reason and showing the "not a legal attestation" notice.
- Long operations (sealing, export) run **off the UI thread** with real progress — never a fake bar.

## 8. Acceptance criteria for Milestone 9

1. New numbered migration applies cleanly on an existing M1–M8 DB and is idempotent.
2. **Readiness check** reports real blockers (unsigned WPs, open review notes, unapproved reports, unresolved findings, unverified chain) from real queries; a soft override requires a recorded, audited justification; hard-invalid states cannot be sealed (tested).
3. **Freeze enforces read-only** at the service layer **and** the DB layer — a write against an archived engagement raises (tested), not merely hidden in the UI.
4. **Sealed archive** is integrity-checked (sha256 manifest + top-level content hash), contains DB slice + documents + faiss + reports, supports optional encryption, and its manifest is deterministic (tested).
5. **Audit chain re-verifies from the archive** — sealing preserves, never breaks, the M1 hash chain (tested).
6. **Retention/assembly periods** are configurable, sourced, `verified:false`; **nothing auto-deletes** — the retain-until date is surfaced for auditor action (reviewed/documented; grep guards against a hardcoded period-as-law).
7. **Audit-file export** round-trips: seal → export → a fresh integrity check verifies the exported archive (tested).
8. **Read-only historical access**: documents, findings, working papers, and reports of an archived engagement are all immutable (tested per subsystem).
9. **Reopen** is RBAC-gated (fail-closed), audited, records a reason, and preserves the prior sealed archive (tested).
10. **Engagement isolation**: an archive of Engagement A contains no Engagement B data (tested); every archival action writes a hash-chained audit event and the chain still verifies; `tests/test_architecture.py` passes (archive/manifest logic testable, no ORM in UI, no module > ~400 lines); the app launches and the full **readiness → freeze → seal → browse read-only → export → reopen** flow is manually exercised and reported honestly.

Then stop and report before the next milestone (multi-year continuity / roll-forward — creating the next financial year's engagement from a closed one, with opening-balance tie-out and carried-forward findings).

## 9. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification; if something was skipped or unrunnable (lint/mypy aren't installable here), say so plainly.** Update `BUILD_PROGRESS.md`, `DECISIONS.md`, and `SECURITY.md` (record: what goes in the archive; the deterministic manifest + content-hash approach; the read-only enforcement mechanism; that assembly/retention periods are configurable, sourced, `verified:false` and never auto-purged; that a seal is tamper-evident, not a legal attestation; reopen semantics). Absolutely no fake seals, no readiness status that isn't computed from real state, no auto-deletion of audit files, no dead buttons. If a piece can't be done properly, leave it out and say why.

**Begin the engagement archival, freeze & retention subsystem. Close the audit file into a tamper-evident, read-only, integrity-sealed record — and be honest that a seal is a control, not a legal signature, and that the app never destroys audit documentation on its own.**
