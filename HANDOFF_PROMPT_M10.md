# FinAuditPro — Milestone 10 Handoff Prompt (Multi-Year Continuity & Roll-Forward)

> Copy everything below the line into the coding agent (Antigravity / Gemini).
> This assumes Milestones 1–9 are merged, tested, and the app launches end to
> end (through engagement archival & retention). This milestone was flagged as
> deferred back in M4 ("Carried Forward … model the reference even if cross-year
> navigation UI is thin for now") and it depends on M9: you roll a NEW year's
> engagement forward **from a closed/archived prior-year engagement**. If M9 is
> incomplete, finish it first — you cannot roll forward from a file that was
> never closed.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the
offline-first, privacy-first audit intelligence desktop app for Indian audit
practice. Milestones 1–9 are complete. **Milestone 10 is Multi-Year Continuity &
Roll-Forward** — creating the next financial year's engagement for the **same
client** from the prior year's closed engagement: carrying forward the permanent
file and re-usable planning as **drafts for re-assessment**, linking **opening
balances to the prior year's audited closing balances** with a tie-out check,
and pulling **carried-forward findings** with provenance.

This milestone is **deterministic — no new AI is used here** (carried
AI-assisted findings keep their M5 badges/citations). Every prior principle
still binds: **engagement isolation is absolute** — this operates _within one
client across years_ and must never cross clients; `domain/` stays pure; UI
touches no ORM/session; fail-closed RBAC; money in paise/`Decimal`; hash-chained
audit event for every mutation; **no fabricated data**; **never say "done"
without verification.**

## 0. Ground truth: environment + the TWO hard constraints for this milestone

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**,
venv at `.venv`, **no PyPI network access**. **No new external dependency is
required** — this is domain logic + persistence + UI (like M4/M6), which is
exactly why the tie-out math and the isolation must be tested hard. Reuse the
**M1 Indian fiscal-year value object** (FY = 1 Apr–31 Mar, labelled e.g.
`2025-26`) — do not re-implement or hardcode FY logic elsewhere. Reads from a
prior-year **sealed archive (M9)** must be **read-only** (`mode=ro` /
`query_only`, verified in M9) — roll-forward never mutates a sealed file.

**Hard constraint #1 — roll-forward NEVER fabricates opening balances and NEVER
carries prior-year conclusions as current** (this milestone's version of the
recurring rule; the most important one here):

> You are an engineering student, not a CA. Opening balances and comparatives
> are governed by auditing standards (in India, **SA 510 Initial Audit
> Engagements — Opening Balances** and **SA 710 Comparative Information**) and
> are the **auditor's responsibility to verify** — they are not something the
> software asserts. → The new year's **opening balances are linked to the prior
> year's _audited closing balances_** (from the prior **closed** engagement's M3
> datasets), and the app computes a **tie-out** (opening vs prior closing, in
> paise) that it **surfaces for the auditor to confirm** with a `verified:false`
> flag — never an auto-assertion, never an invented number. Everything else
> rolled forward (risk register, materiality methodology, procedure programs,
> client profile) is a **starting draft explicitly marked "carried from FY X —
> review for current year,"** not a pre-formed conclusion. Prior-year
> **conclusions, sign-offs, and current-year evidence are NOT copied.**

**Hard constraint #2 — roll-forward is a controlled, audited copy _within a
single client_, into a NEW engagement** (isolation + immutability of the past):

> A roll-forward must only ever draw from a **prior engagement of the same
> client**; a test must prove it cannot pull another client's data. It writes
> into a **new engagement** for the next FY and **never mutates the sealed
> prior-year archive (M9)** — reads from the archive are read-only, and the
> prior archive's content hash must be unchanged afterward. Every rolled item
> records its **source engagement + source FY** as provenance.

## 1. Scope of Milestone 10 — one coherent vertical, top to bottom

**From a client's closed prior-year engagement → create the next FY engagement →
choose what to roll forward (permanent-file documents, client/entity profile,
risk register as drafts, materiality methodology, procedure programs,
carried-forward findings) → link and tie out opening balances to the prior
year's audited closing → the new engagement is a normal Active engagement with
visible prior-year links and comparatives available.**

**Out of scope this milestone:** report comparative _formatting_ beyond making
prior-year figures available (M7 already generates reports; here you just expose
the linkage/data); packaging & distribution (next milestone); any new AI.

## 2. The roll-forward mechanism — a deterministic, audited copy into a new engagement

- Triggered from a **closed (M9-archived) prior-year engagement** of a client,
  it creates a **new engagement** for the next FY (using the M1 FY value object)
  and copies the auditor-selected, re-usable content:
  - **Carries** (as re-assessable drafts, each marked "carried from FY X —
    review", with source provenance): permanent-file documents (M2),
    client/entity master data, the **risk register** (as _unassessed /
    for-review_ — inherent/control ratings reset or flagged for re-assessment,
    never presented as this year's conclusion), the **materiality
    methodology/benchmark choice** (the _method_, not the prior amounts as final
    — the new year's figures are recomputed), and **procedure
    programs/templates**.
  - **Does NOT carry**: prior-year conclusions, sign-offs, review notes,
    current-year evidence, or any prior-year period-specific amount presented as
    if current.
- The operation is **audited** (hash-chained) and records exactly what was
  carried, from which engagement/FY, by whom, and when.

## 3. Opening balances & comparatives — link + tie-out, not assertion

- Link the new engagement's **opening balances** to the prior year's **audited
  closing balances** (from the prior closed engagement's M3 datasets, read
  read-only from the M9 archive where applicable). Compute a **tie-out**
  (opening == prior closing) in **paise/`Decimal`**, and **surface mismatches
  loudly** for the auditor — the auto-tie is flagged `verified:false` and the
  auditor confirms it (SA 510).
- Make prior-year figures available as **comparatives** to M3 analytics and M7
  reports for the new engagement (SA 710) — as linked data the auditor uses,
  never an auto-generated comparative conclusion.

## 4. Carried-forward findings — provenance-linked starting points

- A prior-year finding with status **Carried Forward** (or still open) can be
  pulled into the new engagement as a **new finding** carrying a reference to
  its source engagement/FY and its history; **M5 AI-assisted findings retain
  their AI badge + citations**. It is a starting point the auditor
  **re-assesses** this year — never auto-resolved or auto-concluded.

## 5. Data model additions (new numbered migration on the existing DB)

Engagement gets `prior_engagement_id` (self-referential, nullable) and
`fiscal_year`; `roll_forward_records` (new_engagement_id, source_engagement_id,
source_fy, items_carried summary, performed_by, timestamp); **provenance
columns** (`source_engagement_id`, `source_fy`) on rolled entities (risks,
procedures, carried findings, opening-balance links); opening-balance links +
tie-out results (paise, `verified:false`). Reuse the M1 hash-chained audit-event
mechanism for every mutation. Migration applies cleanly on an existing M1–M9 DB
and is idempotent. Reads from the prior sealed archive are strictly read-only.

## 6. UI (professional, dense, keyboard-first — consistent with earlier milestones)

- **"Create next year from…"** action on a closed engagement → a **roll-forward
  wizard**: checkboxes for what to carry, each item labelled **"carried from FY
  X — review for current year."**
- **Opening-balance tie-out screen**: prior closing vs new opening per account,
  **mismatches highlighted loudly**, the auto-tie badged `verified:false` for
  auditor confirmation.
- The new engagement shows a **"Prior year" panel** with links back to the
  (read-only) prior engagement and available comparatives; carried items are
  visibly **badged** with their source FY.
- Long operations run **off the UI thread** with real progress.

## 7. Acceptance criteria for Milestone 10

1. New numbered migration applies cleanly on an existing M1–M9 DB and is
   idempotent.
2. Roll-forward creates a **new engagement for the next FY** and **never mutates
   the sealed prior-year archive** — the prior archive's content hash is
   unchanged afterward (tested).
3. Rolled items are marked **"carried from FY X — for review,"** carry source
   provenance, and prior-year **conclusions/sign-offs are NOT copied** (tested).
4. **Opening-balance tie-out**: opening links to prior audited closing; the
   tie-out computes matches/mismatches in paise and **surfaces mismatches
   loudly**; the auto-tie is `verified:false` for auditor confirmation (tested).
5. **Carried-forward findings** pull through with provenance + history
   reference; M5 AI findings retain their badge/citations (tested).
6. **No hardcoded FY logic** beyond the configurable M1 Indian FY value object;
   **no fabricated opening balances** (reviewed/documented).
7. **Cross-client isolation is absolute**: roll-forward only within the same
   client; a test proves it cannot pull another client's data.
8. **Comparatives** (prior-year figures) are available to M3 analytics / M7
   reports for the new engagement (tested linkage).
9. Every roll-forward action writes a **hash-chained audit event** and the chain
   still verifies; reads from the prior archive are read-only.
10. `tests/test_architecture.py` passes (tie-out math in `domain/`, pure; no ORM
    in UI; no module > ~400 lines); the app launches and the full **close prior
    year → roll forward → tie out opening balances → carry findings → work the
    new year** flow is manually exercised and reported honestly.

Then stop and report before the final milestone (packaging & distribution — a
distributable build, first-run experience, and honest handling of the steps that
need network access or the user's Apple Developer credentials).

## 8. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise
the workflow, inspect your own code, fix, continue. **Never say "done" without
verification; if something was skipped or unrunnable (lint/mypy aren't
installable here), say so plainly.** Update `BUILD_PROGRESS.md` and
`DECISIONS.md` (record: what carries vs what does not; that carried items are
re-assessable drafts, not conclusions; the opening-balance tie-out approach and
its `verified:false` auditor-confirmation; provenance modelling; that
roll-forward never mutates a sealed archive and never crosses clients).
Absolutely no fabricated opening balances, no prior-year conclusions presented
as current, no cross-client leakage, no dead buttons. If a piece can't be done
properly, leave it out and say why.

**Begin the multi-year continuity & roll-forward subsystem. Carry forward the
re-usable file as drafts for re-assessment; tie opening balances to the prior
audited closing for the auditor to confirm; never invent a balance, never copy a
conclusion, never cross a client boundary, never touch a sealed archive.**
