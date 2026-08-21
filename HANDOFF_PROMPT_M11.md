# FinAuditPro — Milestone 11 Handoff Prompt (Packaging, Distribution & First-Run) — TRUE FINAL

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestones 1–10 are merged, tested, and the app launches and runs end to end. This is the true
> final milestone — making FinAuditPro **distributable**. It is unusual and **honesty-critical**:
> the build/signing tools are NOT fully available in this environment, so much of this milestone is
> "build what genuinely runs offline, author the real tooling for the rest, and **honestly report
> what is blocked** on network access or the user's Apple Developer credentials." Do not fake a build.

---

You are completing FinAuditPro, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1–10 are built. **Milestone 11 is Packaging, Distribution & First-Run**: a robust first-launch/onboarding experience and environment self-check, a real from-source run path, the build tooling for a distributable (spec + scripts, ready to run when tools/network are available), and honest, ready-to-run (but not executed) signing/notarization/installer procedures.

The product's highest principle applies more sharply here than anywhere: **DO NOT CREATE FAKE FUNCTIONALITY** and **never say "done" without verification.** A correctly-authored build script that you honestly report as *"not run — PyInstaller can't be installed offline"* is a success. A committed binary, a claimed signature, or a fabricated "notarized ✓" is a failure of the whole project's integrity. Every prior principle still binds (offline-first; engagement isolation; fail-closed RBAC; `domain/` pure; UI touches no ORM/session).

## 0. Ground truth: environment + the ONE overriding honesty constraint

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access**, **macOS 26.6.2 (Apple Silicon)**. Verified (re-verify in your sandbox):
- **PyInstaller is NOT installed** (`importlib.util.find_spec('PyInstaller')` → `False`; no `pyinstaller` on `PATH`) and **cannot be pip-installed** here (no network). **py2app is likewise NOT installed.** → **You cannot produce a frozen/standalone binary in this sandbox.** State this plainly; do not fake it.
- **`codesign` (`/usr/bin/codesign`) and `xcrun` (`/usr/bin/xcrun`) ARE present** — but code-signing needs a **Developer ID certificate** and notarization needs **Apple ID + notarytool credentials**, none of which are available here and **must never be invented or hardcoded**.
- **`tesseract` is present via Homebrew** (`/opt/homebrew/bin/tesseract`) — so OCR works from source, but it is a system binary; **bundling/redistributing it** into a self-contained app has its own licensing (Apache-2.0) and per-language `traineddata` considerations — treat as a documented follow-up, not a fake bundle.
- The **from-source run path IS fully runnable here** (the app launches from `.venv`), so the first-run experience, self-check, and INSTALL flow are real, testable deliverables **now**.

**The overriding honesty constraint:**

> Where a step needs network (installing PyInstaller) or the user's private credentials (Apple Developer ID, notarytool), you must **author the correct, ready-to-run tooling and document the exact commands**, then **STOP and report that step's status honestly** as *blocked: needs network* or *blocked: needs the user's Apple Developer credentials* — and let the user run it themselves. **Do not** commit a bogus `.spec`-as-if-built, **do not** claim anything was signed or notarized, **do not** fabricate a version string, build hash, or artifact. A build that didn't happen is reported as not-happened.

## 1. Scope of Milestone 11 — split explicitly into "buildable now" vs "prepared but blocked"

**Buildable and verifiable now (do these for real):** first-run bootstrap + onboarding; a launch-time environment self-check; app data-directory setup; a settings screen for the LM Studio endpoint/model and the cloud-AI opt-out; a version/build-info module with real values; INSTALL docs for the from-source run; the PyInstaller/py2app spec + build script + pinned requirements (authored, not executed).

**Prepared but blocked (author + document + honestly mark, do NOT execute or fake):** running PyInstaller/py2app to emit a binary; code-signing; notarization + stapling; bundling tesseract; building a `.dmg`/installer.

**Out of scope:** any new product feature; auto-update infrastructure (document a plan only); Windows/Linux packaging (note as follow-up — this environment is macOS).

## 2. First-run & onboarding (real, buildable now)

- On first launch: create the app data directories (SQLite DB, document store, faiss index dir, and a **writable `MPLCONFIGDIR`** per the M7/M8 note), run the M1 migration runner to current, and initialise cleanly — reporting any dir/permission failure honestly rather than swallowing it.
- A short onboarding flow: create the firm, the first user/role (fail-closed RBAC from M1), and confirm the offline/privacy posture (M8) — no cloud calls unless the user later explicitly opts in.

## 3. Environment self-check (real, buildable now — and it must be honest)

- On launch (and re-runnable from settings), check and report the **real** status of each prerequisite: Python version; required packages present; **tesseract** present (else OCR disables with an honest message, per M2); **LM Studio** reachable (`GET /v1/models`) and whether `deepseek-r1-distill-qwen-14b` + `nomic-embed-text` are loaded (else AI features degrade honestly, per M5/M8); data dirs writable. **Never a fake "all good"** — each line reflects an actual probe, with actionable remediation text.

## 4. Settings & version info (real, buildable now)

- A settings screen to configure the **local LM Studio endpoint/model** and the **cloud-AI opt-out** (off by default; opting in shows the M8 privacy warning).
- A **version/build-info** module returning real values (app version, git commit if available, Python version). No fabricated build hash.

## 5. Build tooling (author real, runnable-later — honestly marked as not run)

- A maintained **PyInstaller spec** (or py2app `setup.py`) that *would* build the app on Apple Silicon, plus a **build script** and **pinned requirements**, with correct handling of the frozen context (data dirs, `MPLCONFIGDIR`, bundled resources). Include the approach for **tesseract + traineddata** (bundle vs external prerequisite) with its licensing note.
- These are **correct and ready** but **were not executed here because PyInstaller cannot be installed offline** — say exactly that in the report and in `PACKAGING.md`.

## 6. Signing, notarization & installer (document + script, do NOT execute or fake)

- Provide **ready-to-run scripts** with **placeholders** for the user's Developer ID + credentials: `codesign` with hardened runtime + entitlements, `xcrun notarytool submit`, `xcrun stapler staple`, and a `.dmg` build step. Document the exact sequence.
- Mark every one of these **"requires the user's Apple Developer account / not run here."** The agent must **not** invent certificates, must **not** claim it signed or notarized anything.

## 7. Documentation (real)

- **INSTALL.md** — the from-source run (create venv, install pinned deps, install the tesseract binary, set up LM Studio + the two models, launch) — verified to actually work on this machine.
- **PACKAGING.md** — the full build → sign → notarize → dmg procedure, with each network-/credential-gated step clearly marked as such.
- Update **BUILD_PROGRESS.md**, **DECISIONS.md**, and **SECURITY.md**, and produce a **final honest product status across all 11 milestones**: what was built, what runs from source, and precisely what remains blocked on network access or the user's Apple credentials.

## 8. Acceptance criteria for Milestone 11

1. **First-run bootstrap** creates all app data dirs (including a writable `MPLCONFIGDIR`) and runs migrations to current on a clean machine (tested); dir/permission failures are reported, not swallowed.
2. **Launch self-check** reports each prerequisite's REAL status (Python, packages, tesseract, LM Studio reachable + models loaded, writable dirs) with honest remediation — verified with a prerequisite deliberately absent (e.g. LM Studio down shows a truthful "unavailable", not a fake OK).
3. **LM Studio + model detection** degrades honestly when absent; **cloud AI stays opt-in/off by default** with the M8 warning (tested).
4. **Tesseract detection** works; OCR disables with an honest message when it's missing (tested).
5. A maintained **PyInstaller/py2app spec + build script + pinned requirements** exist and are correct — with an explicit, honest note that **they were NOT executed because PyInstaller can't be installed offline** (documented, not faked).
6. **Signing/notarization/dmg** are provided as ready-to-run scripts with credential placeholders, clearly marked **"requires the user's Apple Developer credentials / not run here"**; nothing claims to have signed or notarized anything (reviewed).
7. **Tesseract bundling** is either implemented or documented as an external prerequisite with its licensing noted — honestly, no fake bundle.
8. **Version/build-info** returns real values; no fabricated build hash.
9. **INSTALL.md** lets a fresh user run the app from source successfully (manually verified end-to-end on this machine); **PACKAGING.md** documents the blocked steps honestly.
10. `tests/test_architecture.py` passes; the app launches; `BUILD_PROGRESS.md`/`DECISIONS.md`/`SECURITY.md` are updated; and a **final honest status report** across all 11 milestones lists exactly what was built, what runs from source, and what is blocked on network/Apple credentials.

This is the true final milestone. There is no "next" — after it, deliver the final, honest, end-to-end account of the product: what works and was verified how, what is mock- vs live-tested, what is deferred, what could not be run in this environment (lint/mypy, PyInstaller, signing/notarization), and every `verified:false` statutory default still awaiting a CA's confirmation.

## 9. Process & honesty (unchanged, non-negotiable — and it is the whole point of this milestone)

Work in coherent steps; after each, run the test suite, launch the app, exercise the flow, inspect your own code, fix, continue. **No fake binary. No fake signature. No fake notarization. No invented version or build hash. A step that is blocked on network or the user's credentials, reported honestly as blocked, is the correct outcome — not a failure to hide.** Update `BUILD_PROGRESS.md`, `DECISIONS.md`, and `SECURITY.md`. If a piece can't be done properly in this environment, author the ready-to-run tooling, document it, mark it blocked, and say why.

**Begin the packaging, distribution & first-run milestone. Build everything that genuinely runs offline, author the real tooling for everything that doesn't, and tell the exact truth about which is which.**
