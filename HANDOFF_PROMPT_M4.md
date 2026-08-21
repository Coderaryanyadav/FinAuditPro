# FinAuditPro — Milestone 4 Handoff Prompt (Risk, Materiality, Audit Procedures & Findings)

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestones 1 (Firm→Client→Engagement→Dashboard), 2 (Documents & OCR), and 3 (Financial import
> & deterministic analytics) are merged, tested, and the app launches. If any is incomplete,
> finish it first — do not build the planning layer on an unfinished foundation.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1–3 are complete: firm/client/engagement/dashboard, the document subsystem (upload→OCR→index→search→evidence links), and financial-data import with deterministic analytics that can promote an exception into a structured Finding. **Milestone 4 is the audit planning & execution core: Materiality → Risk Assessment → Audit Procedures → Findings**, all fully traceable.

This milestone is still **100% deterministic — no AI/LLM is used here.** The master brief is emphatic (§11): "Calculations must be deterministic and visible. Do not hide accounting calculations behind an LLM." Materiality and risk are exactly the kind of thing that must be transparent, reproducible, and versioned. AI comes in the milestone *after* this one.

Everything from earlier milestones still binds: clean layer boundaries; UI touches no ORM/session; **money is never a `float`** (integer paise / `Decimal`); fail-closed RBAC in the service layer; a hash-chained audit event for every mutation; every object scoped to exactly one engagement with no cross-engagement/client leakage.

## 0. Ground truth: environment & the ONE new hard constraint

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access** (build only with installed packages: PySide6, SQLAlchemy, pydantic, pytest — all already used). **This milestone introduces no new external dependency.** It is pure domain logic + persistence + UI, which is exactly why it must be tested hard.

**The new hard constraint — treat it like M3's "no hardcoded holidays" rule:**

> **Materiality percentages, risk models, and benchmark choices are matters of professional judgement guided by auditing standards (in India, SA 320 for materiality; SA 315 for risk) — they are NOT fixed statutory numbers.** You are an engineering student, not a CA: **do not hardcode a percentage as if it were law.**

Concretely:
- Commonly *referenced* benchmark ranges exist (e.g. materiality is often discussed as a small percentage of profit before tax, revenue, or total assets), but the exact percentage is the **auditor's judgement**. → Offer benchmarks and default percentages as **editable suggestions carrying a `source` and a `verified: false` flag surfaced in the UI**, never as a locked-in requirement. The auditor picks the benchmark, enters the amount, and sets the percentages.
- Do not invent false numeric precision for risk (e.g. "inherent 0.7 × control 0.6 = 0.42 audit risk"). The standard model is **qualitative** (High/Medium/Low combined via a matrix). Offer the conventional qualitative matrix, make it configurable/versioned, and label it as guidance.
- The **financial-statement assertions** (existence/occurrence, completeness, accuracy, valuation & allocation, rights & obligations, cutoff, classification, presentation & disclosure) are stable, standards-defined vocabulary and are fine to include as an enum — but attribute them to the assertions framework, don't dress them up as bespoke law.

If you are ever unsure whether something is a fixed rule or a judgement call, treat it as a **judgement call the auditor controls**, and say so in the UI.

## 1. Scope of Milestone 4 — one coherent vertical, top to bottom

**Set materiality → build the risk register (with assertions) → design procedures linked to risks → execute procedures → record findings (unified model) → navigate the full traceability graph.**

The payoff of this milestone is **traceability made real**, in both directions:

```
Risk  →  Procedure  →  Evidence (document page / transaction row from M2 & M3)  →  Finding  →  Conclusion
Finding  →  Procedure  →  Risk  →  Assertion            (and Finding → Evidence → source document/row)
```

**Out of scope this milestone:** any AI/LLM (next milestone), working-paper *documents* and sign-off workflow (the milestone after — though findings/procedures will later attach to working papers, so design the keys to allow it), and report generation. Build the planning-and-findings core and make it correct and connected.

## 2. Materiality engine — deterministic, transparent, reproducible, versioned

This is a pure-domain calculation. Put the math in `domain/` as tested functions/value objects; the service persists inputs and results; the UI only displays.

- Compute and store the three standard thresholds:
  - **Overall Materiality (OM)** = chosen benchmark amount × chosen percentage (auditor-entered).
  - **Performance Materiality (PM)** = a percentage of OM (auditor-entered; conventionally a haircut).
  - **Clearly Trivial Threshold (CTT)** = a small percentage of OM (auditor-entered).
- **Persist the full reproducible record**: benchmark chosen, benchmark amount (paise), each percentage, the resulting OM/PM/CTT (paise), methodology/notes, the calculation version, the user, and the timestamp. Re-computing from the stored inputs must yield the identical result (a test asserts this).
- **Show the working** in the UI: the formula, the inputs, and the outputs — no hidden steps. All amounts are `Money` (paise), never float; percentages held exactly (Decimal), rounding rule explicit and documented.
- Support **revising** materiality (new version, old versions retained and audited) — auditors revise materiality as the engagement progresses; history must survive.
- Wire CTT/PM back into M3: an exception/finding whose amount is **below CTT** can be flagged "clearly trivial", and amounts crossing PM/OM highlighted — but only as computed indicators the auditor reviews, never auto-conclusions.

## 3. Risk register — identification, assessment, response

- A **Risk** belongs to an engagement and carries: title, description, category (e.g. fraud/SA 240, revenue recognition, going concern, related-party, estimates, IT/general-controls, statutory-compliance — configurable list, not exhaustive law), **affected assertion(s)** (enum from §0), **inherent risk** (H/M/L), **control risk** (H/M/L), derived **risk of material misstatement** via the configurable qualitative matrix, a **significant-risk** flag, and a **planned response**.
- Risks are **linked to procedures** (a risk is addressed by one or more procedures) and ultimately to findings. Provide the join tables.
- Keep the risk model qualitative and honest (see §0) — no fabricated numeric audit-risk scores.

## 4. Audit procedures — the bridge from risk to evidence

- A **Procedure** carries: objective, the risk(s) it responds to, the assertion(s) it covers, procedure type (e.g. inspection, observation, inquiry, confirmation, recalculation, re-performance, analytical procedure), instructions, evidence requirement, **execution status** (Not Started / In Progress / Completed / Not Applicable), result/conclusion, preparer, reviewer, timestamps.
- Procedures **link to evidence** via the Milestone-2 `evidence_links` (a document page / region) **and** to Milestone-3 dataset rows (a transaction / ledger entry / TB line) — so "evidence" is uniformly either a document location or a data row. Extend `evidence_links` if needed to reference a dataset row, keeping one clean evidence abstraction.
- A procedure can raise **Findings** (see §5). Analytical-procedure results from M3 can attach here.

## 5. Findings — one unified structured model, full lifecycle

There must be **exactly one Finding model**, used identically by (a) manual auditor entry, (b) M3's accept-an-exception path, and (c) the future AI path. Do not create a second findings concept.

- Fields: engagement, title, description, category, **severity**, amount (paise, nullable), affected account/area, assertion, linked risk, linked procedure, **evidence** (via evidence_links → document page/row), recommendation, **status**, preparer, reviewer, review status, **source** (`manual` | `deterministic_analytic` | `ai` — and `ai_generated` boolean), timestamps.
- **Status lifecycle** (from the brief §13): `Open → Under Review → Resolved / Accepted / Rejected / Carried Forward`. Model legal transitions explicitly; illegal transitions are rejected in the service layer and audited.
- The M3 "accept exception → Finding" path from Milestone 3 must now write into **this** model with `source=deterministic_analytic`, `ai_generated=false`, and its evidence links intact. If M3 created a provisional findings table, migrate it into the unified model in this milestone's numbered migration.
- **Carried Forward** should capture the prior-year linkage concept (a finding carried from a previous engagement/year) — model the reference even if cross-year navigation UI is thin for now.

## 6. Data model additions (new numbered migration on the existing DB)

Normalized, engagement-scoped, one source of truth each: `materiality_calculations` (versioned, with all inputs + outputs in paise), `risks`, `risk_assertions` (or an assertion set on the risk), `audit_procedures`, `risk_procedure_links`, `procedure_evidence_links` (or extend `evidence_links`), and the unified `findings` (+ `finding_evidence_links`). Reuse the Milestone-1 hash-chained audit-event mechanism for **every** mutation (materiality set/revised, risk created/assessed, procedure status change, finding created/status-changed/reviewed). The migration must apply cleanly on an existing M1–M3 database and be idempotent.

## 7. UI (professional, dense, keyboard-first — consistent with earlier milestones)

- **Materiality panel**: benchmark picker (suggestions labelled as judgement, `verified:false` sources visible), amount + percentage inputs, live computed OM/PM/CTT with the formula shown, save-as-version, and a history of prior versions.
- **Risk register**: dense table (title, category, assertions, inherent/control → RoMM, significant?, response, # linked procedures); create/edit; link to procedures.
- **Procedures**: table + editor (objective, type, risk/assertion links, status, preparer/reviewer, conclusion); attach evidence (document page or dataset row) via a picker that reuses M2/M3.
- **Findings**: unified list across all sources with a visible **source badge** (manual / analytic / **AI** — AI clearly distinguishable per the brief), severity, status; editor with the status-transition control (only legal transitions offered); drill into **evidence** and navigate the traceability graph both ways.
- Strong empty/loading/error states everywhere; every number derived from a real query; no decorative zeros; no dead buttons.

## 8. Acceptance criteria for Milestone 4

1. New numbered migration applies cleanly on an existing M1–M3 DB and is idempotent; any provisional M3 findings table is migrated into the unified model with evidence intact.
2. **Materiality is deterministic & reproducible**: a test computes OM/PM/CTT from stored inputs and asserts exact paise results; recomputing yields identical values; all amounts are paise/`Decimal`, never float.
3. **No hardcoded statutory numbers**: benchmark percentages are auditor-editable, defaults carry a `source` + `verified:false`, and nothing in code or UI presents a percentage as a legal requirement (add a test/grep guarding against a hardcoded "5%"-as-law pattern where feasible; at minimum, review and document).
4. Materiality **revision** creates a new version, retains history, and is audited.
5. **Risk register** supports create/assess with assertions and the qualitative inherent/control→RoMM matrix; significant-risk flag works; risks link to procedures.
6. **Procedures** link to risks + assertions, carry a real status workflow with preparer/reviewer, and can attach **evidence** that is either a document page (M2) or a dataset row (M3) through one unified evidence abstraction.
7. **One Findings model**: manual creation and the M3 accept-exception path both write the same table; `source` and `ai_generated` are set correctly; the status lifecycle enforces legal transitions and rejects illegal ones (tested).
8. **Traceability test**: from a finding, code can navigate Finding → Procedure → Risk → Assertion and Finding → Evidence → source document page / dataset row; a dedicated test asserts the graph resolves.
9. **Engagement isolation**: a test proves risks/procedures/findings/materiality of Engagement A never surface under Engagement B.
10. Every mutation writes a **hash-chained audit event** and the chain still verifies (extend the chain test). `tests/test_architecture.py` still passes (materiality math lives in `domain/`, pure; UI touches no ORM; no module > ~400 lines). The app launches and the full **set materiality → add risk → add procedure → attach evidence → raise finding → walk the traceability graph** flow is manually exercised and reported honestly.

Then stop and report before the next milestone (the local AI subsystem: provider abstraction, embeddings, engagement-scoped RAG, and structured AI findings that use this same Findings model).

## 9. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification; if something was skipped or unrunnable (lint/mypy aren't installable here), say so plainly.** Update `BUILD_PROGRESS.md` and `DECISIONS.md` (record: materiality rounding rule; which benchmark defaults and their sources; the risk matrix used and that it's configurable; finding status-transition rules; how evidence unifies document pages and dataset rows). Absolutely no fabricated figures, no accounting math hidden or approximated, no dead buttons, no TODOs masquerading as implementation. If a piece can't be done properly, leave it out and say why.

**Begin the risk, materiality, procedures, and findings subsystem.**
