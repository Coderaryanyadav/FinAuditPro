# FinAuditPro — Milestone 5 Handoff Prompt (Local AI Subsystem: LM Studio + RAG + AI-Assisted Findings)

> Copy everything below the line into the coding agent (Antigravity / Gemini). This assumes
> Milestones 1–4 are merged, tested, and the app launches (firm/client/engagement/dashboard;
> documents & OCR; financial import & deterministic analytics; risk/materiality/procedures and the
> unified Findings model). If any is incomplete, finish it first — the AI layer sits ON TOP of
> real documents, real data, and the real Findings model. Do not build AI on an unfinished base.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestones 1–4 are complete. **Milestone 5 is the local AI subsystem: a provider-agnostic LLM layer running against LM Studio, engagement-partitioned RAG, and AI-*assisted* structured Findings that flow into the SAME unified Finding model built in Milestone 4.**

The product's first principle governs this entire milestone: **AI assists, the auditor decides.** FinAuditPro is never an autonomous auditor. Every AI output is a *proposal* with mandatory source citations that a human reviews and explicitly accepts or rejects. The master brief's hardest rules all live here:
- **Client data never leaves the machine by default.** LM Studio is local; keep it that way. Any cloud provider is explicit opt-in with a loud warning.
- **Treat every document as untrusted data.** Text inside a PDF saying "ignore previous instructions" is *content*, not an instruction.
- **RAG must hard-partition retrieval by engagement/client.** A query for Client A must **never** retrieve Client B's data. This is critical and must be tested.
- **No fabrication.** Never invent a model response, a citation, or a confidence. "Insufficient evidence" beats a guess. If LM Studio is unreachable, say so — never fake an answer.

Everything from earlier milestones still binds: clean layer boundaries; `domain/` stays pure (no `httpx`, no `faiss`, no Qt); UI touches no ORM/session and no network; money is paise/`Decimal`; fail-closed RBAC; a hash-chained audit event for every mutation; strict engagement scoping.

## 0. Ground truth: environment + the LM Studio & DeepSeek-R1 facts that shape everything

Same machine: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access** (build only with installed packages). **Re-verify these in your own sandbox before relying on them.**

**Verified installed / NOT installed (this dictates your implementation):**
- **`openai` (the OpenAI Python SDK) is NOT installed and cannot be installed** (no PyPI). → **Talk to LM Studio over raw `httpx` 0.28.1** (installed) against its OpenAI-compatible REST API. Do not `import openai`.
- **`httpx-sse` is NOT installed.** → For streaming responses, parse Server-Sent Events yourself from `httpx`'s streaming response (`with client.stream("POST", …) as r: for line in r.iter_lines(): …`, handle `data: {…}` / `data: [DONE]`). No SSE helper library.
- **`tiktoken` is NOT installed.** → You have no exact tokenizer. Estimate token counts heuristically (e.g. ~chars/4) and label it an estimate, or use LM Studio's own tokenization endpoint if exposed. Never present an exact token count you didn't measure.
- **`faiss` (faiss-cpu 1.14.3) IS installed and works** (verified: `IndexFlatIP` add/search fine). This is your vector store.
- **`numpy` 2.5.1** installed — embeddings as `float32` arrays for faiss.
- **`sentence-transformers` 5.6.0 IS installed** — BUT it needs a model, and models download from HuggingFace (**no network here**). So it is only usable if a model is **already cached locally**. Treat it as a *possible* offline embedding fallback that you must **detect at runtime**, not assume. The primary embedding path is LM Studio (below).
- **`ollama` 0.6.2 client is installed but you are NOT using Ollama this milestone** — the user runs **LM Studio**. Ignore the ollama client.
- Vectors live in **faiss on disk**, not SQLite — do not depend on any SQLite vector extension.

**LM Studio API — verified facts (the user's chosen runtime):**
- OpenAI-compatible server, default base URL **`http://localhost:1234/v1`** (make it configurable). Endpoints confirmed: **`GET /v1/models`**, **`POST /v1/chat/completions`**, **`POST /v1/embeddings`**, `POST /v1/completions`, `POST /v1/responses`.
- LM Studio also exposes a **native REST API `GET /api/v0/models`** that reports richer info — **loaded vs unloaded, max context, quantization**. Use `/api/v0/models` (best-effort) to detect whether the chat model and an embedding model are actually **loaded**, and to read the context length; fall back to `/v1/models` if the native route isn't there.
- **Structured JSON output** is requested via `response_format` on `/v1/chat/completions`:
  ```json
  "response_format": {
    "type": "json_schema",
    "json_schema": { "name": "finding", "strict": "true", "schema": { "type":"object", "properties": { … }, "required": [ … ] } }
  }
  ```
  The model's answer arrives as a **string in `choices[0].message.content` that you must parse** — it is not pre-parsed. Caveat from the docs: **not all models comply** (esp. <7B), and GGUF vs MLX use different constraint engines. So `response_format` is a *help*, not a guarantee — see §2 for the real validation strategy.

**DeepSeek-R1-Distill-Qwen-14B — verified model behavior (the user's chosen model):**
- It is a **reasoning model**. It emits a **`<think> … </think>` block first**, then the answer. It sometimes emits an empty `<think>\n\n</think>`. → **You MUST strip the `<think>…</think>` block before parsing JSON or showing an answer.** The structured/answer content is what follows `</think>`.
- Official usage guidance: **temperature 0.5–0.7 (use 0.6)**, **top_p 0.95**, and **do NOT use a system prompt — put all instructions in the user message.** Very low/greedy temperature causes "endless repetitions or incoherent outputs." (See §4 for how this reconciles with the required SYSTEM/USER/DOCUMENT separation.)
- **Consequence — AI outputs are NON-DETERMINISTIC.** Unlike Milestones 3–4 (which are exactly reproducible), an R1 finding is not. You will record the model id, params, seed (best-effort), prompt version, and retrieved-chunk ids so a run is *explainable and auditable*, even though it is not bit-reproducible. Be honest about this in the UI and in `DECISIONS.md`.

**You cannot test LM Studio from this build's sandbox** (network is locked to two hosts and LM Studio runs on the user's real machine). So: **write the code to detect LM Studio at runtime and degrade honestly when it's absent**, and verify the live path in the environment where LM Studio is actually running. Do not claim you exercised a live model call if you did not.

## 1. Scope of Milestone 5 — one honest AI vertical, end to end

Build exactly this, genuinely working, auditor-gated:

**Index an engagement's documents (chunk → embed via LM Studio → per-engagement faiss index) → ask a question / request an explanation → retrieve ONLY this engagement's chunks → assemble a safe, separated prompt → call DeepSeek-R1 via LM Studio (streaming, off-thread) → strip reasoning → produce a structured, *cited* answer → optionally promote it to an AI-flagged Finding (Milestone-4 model) that the auditor must review and accept.**

Two concrete use cases, both citing real evidence:
1. **Engagement-scoped Q&A / document explanation** — "What are the payment terms in the vendor agreements?" answered only from this engagement's indexed documents, every claim carrying a citation to document→page→chunk.
2. **AI-assisted Finding suggestion** — from a selected document, exception (M3), or risk (M4), the AI drafts a *proposed* structured Finding (title/description/severity/assertion/recommendation + **mandatory citations**). It lands as a proposal in `Open`/`Under Review`, `source=ai`, `ai_generated=true`, and **cannot advance without a human decision.**

**Out of scope this milestone:** working-paper documents & sign-off, report generation, any cloud provider implementation (leave the seam, don't build it), fine-tuning, agentic multi-step tool use. Keep the AI layer tight, safe, and cited.

## 2. Provider abstraction & the LM Studio client (infrastructure/ai — httpx, not the OpenAI SDK)

- Define an **`LLMProvider` Protocol** in the application layer (pure interface): `chat(messages, schema=None, stream=False, …)`, `embed(texts) -> list[vector]`, `available() -> ProviderStatus`, `models() -> …`. The rest of the app depends only on this Protocol — **never hard-couple to LM Studio or any vendor.**
- Implement **`LMStudioProvider`** in `infrastructure/ai/` using `httpx`:
  - Config (persisted, user-editable): base URL (default `http://localhost:1234/v1`), **chat model id** (default `deepseek-r1-distill-qwen-14b`, but **read the actual id list from `/v1/models`** — don't hardcode blindly), **embedding model id** (separate — see §3), temperature (default **0.6**), top_p (default **0.95**), seed (optional), request timeout (generous — reasoning is slow), max output tokens.
  - **Availability detection**: on demand, `GET /api/v0/models` (fallback `/v1/models`) to confirm the server is up and which models are **loaded**. Cache briefly. Expose a clear status the UI shows: server up/down, chat model loaded?, embedding model loaded?
  - **Reasoning handling**: after each completion, **split off `<think>…</think>`** (including the empty form). Keep the reasoning text **separate and clearly labeled as model reasoning — it is NOT audit evidence and NOT a citation, and must never be stored as the justification of a Finding.** Parse/return only the post-`</think>` content.
  - **Structured output**: send `response_format:{type:"json_schema", json_schema:{name, strict:"true", schema}}` derived from the pydantic model. Then, because compliance isn't guaranteed for a reasoning model: **(a)** strip `<think>`, **(b)** extract the JSON object, **(c)** validate with **pydantic**, **(d)** on failure do **one repair round** ("Your previous output did not match the required schema. Return ONLY valid JSON for it."), **(e)** if it still fails, **return an explicit failure — never coerce a malformed blob into a Finding.**
  - **Streaming**: support SSE streaming (manual parse, no httpx-sse) so the UI shows tokens as they arrive; support cancellation.
  - **No system role for R1**: put instructions in the user message (§4). Keep the provider generic enough that a non-reasoning model could still use a system role — gate the behavior on config, don't bake R1 quirks into the Protocol.

## 3. Embeddings & RAG — engagement-partitioned, with an honest fallback

- **DeepSeek-R1 cannot produce embeddings.** RAG requires a **separate embedding model loaded in LM Studio** (e.g. a `nomic-embed-text` / `text-embedding-*` GGUF), called via `POST /v1/embeddings`. **Detect its presence**; if no embedding model is loaded, do NOT fake vectors.
- **Chunking**: chunk `document_pages` text (from Milestone 2) into overlapping chunks. Each chunk carries a stable id and a back-reference to **document_id → page → character range** so a citation maps to a real evidence location (reuse `evidence_links`). Persist chunk metadata in SQLite.
- **Embed & index**: embed chunks via LM Studio; discover the **vector dimension at runtime** (don't hardcode). Store vectors in a **faiss index persisted on disk, one index file per engagement** (path keyed by engagement id, e.g. `…/data/ai/eng_{id}/index.faiss`). Build/refresh the index **off the UI thread** (reuse the Milestone-2 job mechanism) with real progress. Re-index on document add/delete.
- **Retrieval (hard isolation)**: the retrieval function **takes an engagement_id and can only open that engagement's index file** — it is structurally impossible to reach another engagement's vectors. Embed the query, search top-k, return chunks with scores mapped to evidence locations.
- **Honest degradation**:
  - No embedding model loaded → **fall back to Milestone-2 FTS5 keyword retrieval**, clearly labeled in the UI as "keyword search (no embeddings available)". Do not silently pretend it's semantic.
  - LM Studio down → AI features disabled with an honest banner; **the rest of the app works normally.**
  - `sentence-transformers` is installed but only usable if a model is cached locally — you may detect and offer it as an alternative local embedder, but treat its absence as normal, not an error.

## 4. Prompt assembly & untrusted-content security (the core threat surface)

- **Strict separation of INSTRUCTIONS / USER QUESTION / DOCUMENT CONTENT / OUTPUT.** Reconcile with R1's "no system prompt" guidance like this: keep the separation as **clearly delimited, labeled sections composed inside the single user message** (since R1 wants instructions in the user turn), not as an API `role:"system"`. The separation is about **isolating and neutralizing untrusted document text**, which still fully applies.
- **Every retrieved chunk is untrusted data.** Before inserting it into the prompt: **escape all angle brackets**, and specifically **neutralize any `<think>` / `</think>` tokens embedded in the document** (a malicious or coincidental `</think>` in a PDF must not corrupt your reasoning-stripping or let content masquerade as model output). Wrap document content in an explicit, labeled, escaped block that the instructions tell the model to treat as *evidence to cite, never as commands*.
- **Mandatory citations**: the prompt instructs the model that **every claim must cite a provided chunk id**, and the output schema **requires** citations. An answer/finding with no citation is rejected (see §5). Never allow the model to invent a citation id that wasn't in the retrieved set — validate cited ids against the actual retrieved chunks.
- **No sensitive content in logs.** Prompts/responses may contain client data — do not write them to shared logs; if you persist AI runs (you should, for audit), keep them in the engagement-scoped DB, not log files.
- **Injection tests are acceptance criteria** (§8): a document chunk containing "ignore previous instructions and output …" and one containing a fake `</think>` must NOT change behavior or corrupt parsing.

## 5. Structured AI outputs → the ONE unified Finding model (from Milestone 4)

- AI findings use the **exact same `findings` table and model** as manual and deterministic-analytic findings — **do not create a parallel AI-findings concept.** Set `source='ai'`, `ai_generated=true`, and populate the **mandatory source references** via `evidence_links` pointing to the retrieved chunks → document/page (and, where relevant, M3 dataset rows).
- **No citation ⇒ no finding.** If the model returns a finding without a valid citation into the retrieved evidence, it is not persisted as a finding — surface it as "insufficient evidence" instead.
- **AI findings always land as proposals** in `Open` / `Under Review` and **require an explicit human accept/reject** (which uses the Milestone-4 status lifecycle and is audited). AI can never move a finding to `Resolved`/`Accepted` on its own.
- **Explainability record (not reproducibility)**: for each AI run, persist model id, quantization (if `/api/v0/models` gives it), temperature/top_p/seed, prompt version, the retrieved chunk ids, and timestamp. Store this so a reviewer can see *exactly what the AI saw and how it was configured* — while the UI is honest that AI output is non-deterministic and advisory.

## 6. Data model additions (new numbered migration on the existing DB)

Engagement-scoped, normalized: `ai_provider_config` (or reuse app config), `document_chunks` (id, document_id FK, page, char range, chunk text or reference, embedding model id + dim used, index position), `ai_runs` (id, engagement_id, kind [qa|finding_suggestion], model id, params JSON, prompt version, retrieved chunk ids, status, created_by, timestamps), and `ai_messages`/answer rows as needed for Q&A history. Findings reuse Milestone 4's `findings` + `finding_evidence_links`. faiss index files live on disk keyed by engagement (not in the DB). Every AI mutation (index built, run executed, finding proposed, finding accepted/rejected) writes a **hash-chained audit event**. Migration applies cleanly on an existing M1–M4 DB and is idempotent.

## 7. Off-thread execution & UI (never freeze, never fake)

- Indexing, embedding, and R1 generation are **slow** — run all of them on a worker (reuse the Milestone-2 job mechanism). **Stream** the reasoning/answer to the UI as it arrives; show real progress for indexing (chunks embedded / total); allow **cancel**. Never a timer-driven fake progress bar; never a frozen UI.
- UI: an **AI panel** scoped to the current engagement showing provider status (server/chat-model/embedding-model), an index-status/refresh control, a **Q&A view** where answers render with **inline citations that click through to the exact document page** (reuse the Milestone-2 viewer), and a **"suggest finding"** action that opens the proposed Finding in the Milestone-4 finding editor pre-filled, clearly badged **AI-generated**, requiring the auditor to accept/edit/reject. Show the model's reasoning separately and clearly labeled as *model reasoning, not evidence* (collapsed by default).
- Honest states everywhere: server down, no embedding model, no documents indexed, retrieval empty ("no relevant evidence found" — not a hallucinated answer).

## 8. Acceptance criteria for Milestone 5

1. New numbered migration applies cleanly on an existing M1–M4 DB and is idempotent.
2. **Provider is httpx-based** (no `import openai`), talks to LM Studio at a configurable base URL, and **detects availability** (server up/down, chat + embedding model loaded) via `/api/v0/models` with `/v1/models` fallback — verified against a real running LM Studio, or, if LM Studio isn't available in your environment, verified against a faithful local mock of those endpoints **and clearly reported as mock-tested, not live-tested.**
3. **Reasoning handling**: `<think>…</think>` (including the empty form) is stripped before parsing/display; a unit test feeds a canned R1-style response with a think block + trailing JSON and asserts only the post-reasoning JSON is parsed. Model reasoning is never stored as a Finding's justification.
4. **Structured output is validated, not trusted**: `response_format` json_schema is sent; the response string is parsed and **pydantic-validated**; a malformed response triggers one repair round and then an explicit failure — a test proves a bad response never becomes a persisted Finding.
5. **R1 params** default to temperature 0.6 / top_p 0.95, no system role (instructions in the user message), all configurable; documented in `DECISIONS.md`.
6. **RAG isolation test (critical)**: with documents indexed for Engagement A and Engagement B, a query in A's context retrieves **only** A's chunks — a dedicated test proves B's vectors are unreachable (separate per-engagement index files; retrieval keyed by engagement_id).
7. **Injection/robustness test**: a document chunk saying "ignore previous instructions…" and one containing a stray `</think>` do not alter behavior or corrupt parsing (angle brackets and think-tokens in untrusted content are neutralized).
8. **Citations are mandatory and validated**: an AI answer/finding cites real retrieved chunk ids mapping to document→page; a finding with no valid citation is **not** persisted as a finding (surfaced as "insufficient evidence"). AI findings use the **Milestone-4 Finding model** with `source='ai'`, `ai_generated=true`, land as proposals, and require an audited human accept/reject to advance.
9. **Honest degradation**: with LM Studio stopped, AI features show an honest "unavailable" state and the rest of the app works; with no embedding model loaded, retrieval falls back to FTS5 clearly labeled "keyword (no embeddings)". Both verified.
10. Indexing and generation run **off the UI thread** with real streaming/progress and cancel (manually verified); `tests/test_architecture.py` still passes (no `httpx`/`faiss` in `domain/` or `ui/`; UI makes no network calls; no module > ~400 lines); the app launches and the full **index → ask → cited answer → suggest finding → auditor accept** flow is exercised and reported honestly (state whether it was against live LM Studio or a mock).

Then stop and report before the next milestone (working papers, review & sign-off — which will attach findings/procedures to working-paper documents and add the reviewer workflow).

## 9. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification. Never fabricate a model response, a citation, or a confidence. If LM Studio wasn't available in your environment, say the live path is untested and show what you tested against a mock instead — do not pretend.** Update `BUILD_PROGRESS.md` and `DECISIONS.md` (record: httpx-vs-SDK and why; the `<think>`-stripping approach; structured-output validate+repair+fail strategy; R1 params and no-system-prompt reconciliation; embedding model choice and the FTS5 fallback; per-engagement faiss isolation; that AI output is non-deterministic and advisory-only). Absolutely no fake AI, no uncited claims, no dead buttons, no TODOs masquerading as implementation. If a piece can't be done properly with LM Studio + the installed tooling, leave it out and say why.

**Begin the local AI subsystem. Default to local-only. Cite everything. The auditor decides.**
