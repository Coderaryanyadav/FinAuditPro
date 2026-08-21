# FinAuditPro — Milestone 6 Handoff Prompt (Working Papers, Review & Sign-off)

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestones 1–5 are merged, tested, and the app launches (firm/client/engagement/dashboard;
> documents & OCR; financial import & deterministic analytics; risk/materiality/procedures &
> the unified Findings model; local AI/RAG against LM Studio). If any is incomplete, finish it
> first — working papers tie the whole audit file together and reference everything below them.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1–5 are complete. **Milestone 6 is Working Papers, Review & Sign-off** — the documentation and control layer that makes the audit file real: a preparer documents work against a procedure/area, links the evidence and findings that support it, a reviewer raises review points, the preparer clears them, and an authorized signer signs off, after which the paper is locked. This is the "maker–checker" backbone of audit quality.

This milestone is **deterministic workflow — no new AI is used here** (though working papers can *reference* AI-assisted findings from Milestone 5, which remain human-accepted per that milestone's rules). The product's principles still govern: **AI assists, the auditor decides**; **no fake functionality** (no sign-off that isn't tied to a real identity, no review status that isn't computed from real state); everything scoped to one engagement; a hash-chained audit event for every mutation; fail-closed RBAC in the service layer; `domain/` stays pure; UI touches no ORM/session.

## 0. Ground truth: environment + the TWO hard constraints for this milestone

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access** (build only with installed packages: PySide6, SQLAlchemy, pydantic, pytest — all already in use). **This milestone introduces no new external dependency.** It is persistence + workflow state machines + UI, which is exactly why the state transitions and the RBAC must be tested hard.

**Hard constraint #1 — documentation structure and statutory periods are configurable, sourced content, NOT hardcoded law** (this milestone's version of M3's "no hardcoded holidays" and M4's "no hardcoded materiality %"):

> You are an engineering student, not a CA. Indian audit documentation is governed by standards (e.g. **SA 230 Audit Documentation**, and quality-management standards) and ICAI requirements, but the **specifics — working-paper index structure, the number of review levels, the documentation *assembly period*, the *retention period*, whether a UDIN is required** — are matters of standards/firm policy that change and that you must not bake into code from memory. → Any such structure, level, or time period is a **configurable, versioned entry carrying a `source`, `effective_from`, and a `verified: false` flag surfaced in the UI**, defaulting to sensible but clearly-unverified values the firm can edit. Working-paper *templates*, if you offer them, load from versioned data files (like the compliance-rules engine), never hardcoded ICAI content presented as fact.

**Hard constraint #2 — an electronic sign-off in this app is NOT a legally-recognized digital signature. Keep that honesty explicitly** (the one genuinely good thing in the old codebase — its `qr_verification.py` stated plainly that its HMAC is not an IT Act 2000 Class 3 PKI DSC and that legal ICAI signing needs a CA-issued hardware token):

> The sign-off you build is an **internal workflow attestation plus a tamper-evident audit record** — "user X, in role Y, signed off working paper Z at time T." It is **not** an IT Act 2000 digital signature (DSC), **not** an ICAI UDIN, and confers no legal validity on any report. Say this clearly in the UI at the point of sign-off and in `DECISIONS.md`. If a UDIN field exists, it is a value the auditor **enters** (from the ICAI portal), never one you generate or validate as if authoritative. **Never fake a legal signature or imply legal effect.**

## 1. Scope of Milestone 6 — one coherent vertical, top to bottom

**Create a working paper (for an area / against Milestone-4 procedures) → document the work → link supporting evidence & findings → preparer submits for review → reviewer raises review notes → preparer clears them → authorized signer signs off → the paper locks → the engagement's review status rolls up, and the full audit trail + traceability is navigable.**

The payoff: the working paper is the node that **ties the whole file together** — procedure (M4) ↔ risk (M4) ↔ evidence (M2 document page / M3 dataset row) ↔ findings (M4 deterministic + M5 AI-assisted, human-accepted) — under a reviewed, signed, locked record with a complete who-did-what-when trail.

**Out of scope this milestone:** report generation and export (next milestone — including spreadsheet/PDF formula-injection escaping, which belongs there), full engagement archival/freeze with statutory retention enforcement (design the lock mechanism so it's *possible* later, but don't build retention-period enforcement now), and any new AI. Keep it to the working-paper lifecycle and the review/sign-off controls, done properly.

## 2. The working paper — a first-class record with an explicit lifecycle

- A **WorkingPaper** belongs to exactly one engagement and carries: an **index/reference** (e.g. a cross-referencing code — structure configurable per #1, not hardcoded), title, **area/section** (e.g. planning, revenue, purchases, cash & bank, payroll — a configurable list), **linked procedure(s)** from Milestone 4, the **preparer's documented work** (structured sections + text; see the content note below), the **conclusion**, preparer, assigned reviewer(s), and timestamps.
- **Content**: do not build a fake WYSIWYG word processor. Model the body as **structured sections + plain/markdown text + linked artifacts** (evidence, findings, procedures). Rich formatting is a later concern; make the linking real now. Record this choice in `DECISIONS.md`.
- **Lifecycle** as an explicit state machine (enforced in the service layer; illegal transitions rejected and audited — mirror the Milestone-4 Findings discipline): `Draft → In Preparation → Submitted for Review → Under Review → (Review Notes Open ⇄ Reworking) → Reviewed → Signed Off → [Locked]`, with `Reopened` returning a locked/signed paper to an editable state via a permissioned, audited action. Define the legal transitions once, test them, and reject the rest.
- A working paper can be **created from a Milestone-4 procedure/area** (pre-filling the objective, risk, assertion links) so the planning work flows naturally into documentation.

## 3. Review workflow, review notes & RBAC (the maker–checker core)

- **Preparer → Reviewer(s)** using the roles established in Milestone 1 (e.g. associate/senior/manager/partner). The **review chain is configurable** (number of levels, which role signs off at which level) — do not hardcode a firm's org structure. A single-level firm and a multi-level firm must both work.
- **Review notes** (a.k.a. review points) are a first-class, tracked object: a reviewer raises a note against a working paper (optionally against a specific section/line), the preparer **responds and clears** it, and it moves `Open → Responded → Cleared` (a reviewer can reopen). Notes are threaded and audited.
- **Hard control: a working paper cannot be signed off while it has open review notes.** Enforce this in the service layer and test it — this is a real audit-quality control, not a UI nicety.
- **RBAC (fail-closed, in the service layer, not by hiding buttons):**
  - A preparer may edit only while the paper is in an editable state (`Draft`/`In Preparation`/`Reworking`) and only papers they're assigned to prepare.
  - A reviewer may raise/clear notes and mark reviewed only when assigned as reviewer.
  - **Segregation of duties**: the preparer of a paper cannot be its final signer (configurable, but default-enforced) — surface and test this. No session ⇒ raise (never a silent bypass).
  - Only roles authorized to sign (e.g. manager/partner, configurable) may sign off; only a higher authority (e.g. partner, configurable) may **reopen** a signed/locked paper.

## 4. Sign-off, locking & the honesty boundary

- **Sign-off** records: the working paper (and its content **hash** at the moment of signing, so the signature is bound to exactly what was signed), the signer's identity and role, the action (`prepared` / `reviewed` / `signed off`), a timestamp, an optional note, and a chained integrity hash. Multi-level sign-offs are an ordered list (prepared-by, reviewed-by, signed-off-by).
- **Locking**: once signed off, the working paper is **immutable** — edits are blocked at the service layer (not just the UI). Any change requires an authorized, audited **reopen**, which creates a new editable version while **preserving the prior signed state and its history** (never destroy the record of what was signed).
- **The honesty boundary (constraint #2)**: at the sign-off action, the UI states plainly that this is an internal workflow attestation and tamper-evident record, **not** a legal DSC/UDIN. Persist that framing. If tampering with a signed paper's content is later detected (content hash ≠ recorded hash), surface it **loudly** — tamper detection is never silent.

## 5. Traceability — the working paper ties the file together

From a working paper, code and UI must navigate to: its **procedure(s)** (M4) → **risk(s)** (M4) → **assertion(s)**; its **evidence** via `evidence_links` → document page (M2) / dataset row (M3); and its **findings** (M4 deterministic + M5 AI-assisted). Reuse the existing `evidence_links` abstraction — do not invent a parallel one. A dedicated test asserts the graph resolves: **WorkingPaper → Procedure → Risk → Evidence(doc page / dataset row) → Finding**, and that an AI-generated (M5) finding can be attached to a working paper and shows its AI badge and citations.

## 6. Data model additions (new numbered migration on the existing DB)

Normalized, engagement-scoped, one source of truth each: `working_papers` (with index/ref, area, status enum, linked procedure(s), conclusion, preparer, timestamps), `working_paper_sections` (if you model the body as sections), `working_paper_evidence_links` (or extend `evidence_links` to target a working paper), `working_paper_links` to procedures/risks/findings (join tables), `review_notes` (working_paper_id, raised_by, section ref nullable, text, status, response, cleared_by, timestamps), and `sign_offs` (working_paper_id, level/role, user, action, content_hash, integrity hash, note, timestamp). Reuse the Milestone-1 hash-chained audit-event mechanism for **every** mutation (create, edit, submit, note raised/responded/cleared, reviewed, signed off, reopened). The migration applies cleanly on an existing M1–M5 DB and is idempotent.

## 7. UI (professional, dense, keyboard-first — consistent with earlier milestones)

- **Working-papers list** per engagement: dense table (index/ref, title, area, status, preparer, reviewer, **open-review-notes count**, last action, signed?), filterable by status/area/preparer/reviewer; strong empty/loading/error states.
- **Working-paper editor**: structured sections + text; panels to **link evidence** (reuse the M2 document viewer / M3 dataset row picker), **link procedures/risks** (M4), and **attach findings** (M4/M5, with the M5 AI badge + citations visible). Preparer edits and **submits for review**.
- **Review view**: reviewer sees the paper + its linked evidence, **raises review notes** (threaded, optionally anchored to a section), and marks **reviewed** — with the control that **sign-off is blocked while notes are open**. Preparer sees open notes, responds, and clears them.
- **Sign-off**: an authorized signer signs, sees the **"not a legal DSC/UDIN"** notice, and the sign-off (who/role/when + content hash) is displayed on the now-**locked, read-only** paper with a clear locked banner and an audited **reopen** for permitted roles.
- **Review status roll-up**: the engagement/dashboard shows **real** counts (e.g. papers signed off / total, open review notes) derived from queries — never a decorative number.

## 8. Acceptance criteria for Milestone 6

1. New numbered migration applies cleanly on an existing M1–M5 DB and is idempotent.
2. **Lifecycle enforcement**: legal working-paper transitions succeed and illegal ones are rejected and audited (tested), including the `Reopened` path preserving prior signed history.
3. **Open-notes control**: a working paper with any open review note **cannot** be signed off (service-layer enforced, tested).
4. **RBAC / segregation of duties (fail-closed)**: a preparer cannot sign off their own paper at the final level (default-enforced, configurable); only authorized roles sign; only a higher authority reopens; no session ⇒ raise — all tested.
5. **Review notes** raise → respond → clear (and reviewer reopen) works and is fully audited.
6. **Sign-off binds to content**: the signature records the content hash at signing; altering a signed paper's content is detected and surfaced loudly (tamper detection), and the UI/DB state plainly that sign-off is **not** a legal DSC/UDIN (assert the disclaimer text exists — e.g. a test/grep).
7. **Locking**: a signed-off paper is immutable at the service layer (not just UI); reopen is permissioned, audited, and preserves the prior signed record.
8. **Traceability test**: WorkingPaper → Procedure → Risk → Evidence(document page / dataset row) → Finding resolves; an M5 AI-assisted (human-accepted) finding attaches to a working paper and displays its AI badge + citations.
9. **Engagement isolation**: working papers, review notes, and sign-offs of Engagement A never surface under Engagement B (tested). No statutory structure/period/UDIN is hardcoded — configurable, sourced, `verified:false` (reviewed and documented).
10. Every mutation writes a **hash-chained audit event** and the chain still verifies (extend the chain test). `tests/test_architecture.py` still passes (workflow/state logic testable, UI touches no ORM, no module > ~400 lines). The app launches and the full **create → document → link evidence/findings → submit → raise & clear notes → sign off → lock → reopen** flow is manually exercised and reported honestly.

Then stop and report before the next milestone (reporting & export — assembling findings/working papers into an auditor-reviewed report, with spreadsheet/PDF formula-injection escaping and the same "not a legal signature" honesty on any generated document).

## 9. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification; if something was skipped or unrunnable (lint/mypy aren't installable here), say so plainly.** Update `BUILD_PROGRESS.md` and `DECISIONS.md` (record: working-paper content model choice; the configurable review-chain and index structure and their unverified defaults + sources; segregation-of-duties default; sign-off = internal attestation, not a legal DSC/UDIN, and how content-hash binding works; lock/reopen semantics). Absolutely no fake sign-offs, no review status that isn't computed from real state, no dead buttons, no TODOs masquerading as implementation. If a piece can't be done properly, leave it out and say why.

**Begin the working papers, review & sign-off subsystem. Maker prepares, checker reviews, an authorized signer signs — and the app is honest that this is a workflow control, not a legal signature.**
