# MockMentor — Design Doc

**Author:** Kunal Poonia
**Program:** 2nd Year B.Tech CSE-AIDE Summer Internship 2026 · Segment 3 (Foundations of Applied Machine Learning) · Problem Statement **I2 — Document Q&A / RAG**
**Status:** As-built (reconciled with what shipped). The original 1-page design doc was submitted 24 June; this is the final version updated to match the delivered system.

---

## 1. Problem

Most "practice interview" tools do one of two unhelpful things: they ask static,
pre-written questions with no real feedback, or they let a language model grade
answers from its **own general knowledge** — which means the grade has no
traceable connection to what the student actually studied, and can be confidently
wrong.

MockMentor addresses this with Retrieval-Augmented Generation (RAG): every
grading decision is grounded in a real passage retrieved from the student's own
course material. The student answers a question, the system retrieves the
relevant source chunk, and a local LLM grades the answer **against that
passage**, then generates an adaptive follow-up that targets whatever the answer
missed.

## 2. Goals and non-goals

**Goals**
- Grade answers **grounded in retrieved source material**, not the model's
  unverified opinion, and show the student the exact sources used.
- Generate **adaptive follow-up questions** based on how the answer scored.
- Run **fully locally** — zero API cost, no data leaving the machine.
- Prove the pipeline **generalizes** beyond one corpus (a second subject).

**Non-goals**
- Full-textbook coverage — the corpus is deliberately scoped to 5 chapters.
- Code-writing / auto-graded coding questions — questions are conceptual so a
  local model can grade them reliably.
- An always-on hosted URL — the tool runs locally on demand (see §7).
- Persisting user accounts or cross-session history — sessions are in-memory.

## 3. Approach (the RAG pipeline)

```
source material → ingest (chunk) → embed → ChromaDB
                                                   │
student answer + question ──► retrieve top-k chunks ──► grade against chunks (LLM)
                                                   │
                              verdict · score · explanation · model answer
                              · sources · adaptive follow-up ──► web UI
```

The build step (ingest → embed) runs once. At grade time, only retrieve → grade
runs. The one rule that makes this genuinely RAG: the grading prompt instructs
the model to judge **only** against the retrieved passages
([ADR-001](./adr/ADR-001-grounded-grading.md)).

## 4. Tech choices

| Component | Choice | Rationale |
|---|---|---|
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) | Small (~80 MB), fast on CPU, ChromaDB's default, no API key |
| Vector store | ChromaDB (persisted to `chroma_db/`) | Embedded, no server process, one collection per subject |
| Grading LLM | `qwen3:8b` via Ollama (`llama3.1:8b` fallback) | Fully local, zero cost, fits 6 GB VRAM; thinking mode helps judge partial answers |
| Backend | Flask (`server.py`) | Small JSON API bridging the browser to the Python pipeline |
| Frontend | Single-page HTML/CSS/JS (`UI/index.html`) | Self-contained liquid-glass SPA; no browser framework needed |

Rationale for the fully-local stack over a paid API is recorded in
[ADR-002](./adr/ADR-002-fully-local-stack.md); chunking parameters in
[ADR-003](./adr/ADR-003-chunking-strategy.md).

## 5. Scope

- **Subject #1 — Operating Systems:** 5 selected OSTEP chapters (Intro to OS,
  Scheduling, Address Spaces, Concurrency Intro, Concurrency Problems/Deadlocks),
  ingested by page range → 79 chunks.
- **Subject #2 — DSA (mini-extension):** 9 self-authored interview-pattern notes,
  ingested from markdown by `## ` headers. Added to prove the pipeline
  generalizes with only a per-subject config change, not a rewrite
  ([ADR-004](./adr/ADR-004-os-first-dsa-extension.md)).
- Each subject offers topics with difficulty labels; the model's follow-ups drive
  a session adaptively from the chosen seed question.

## 6. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Local 8B model grades inconsistently / hallucinates | Ground grading in retrieved chunks; explicit "only use context" prompt; `temperature=0.2`; scoped corpus |
| qwen3 `<think>` output breaks JSON parsing | `/no_think` prompt + Ollama `format="json"` + defensive `<think>`-strip and outermost-`{...}` extractor in `evaluate.py` |
| Wrong chunk retrieved → grade grounded in wrong passage | Retrieval sanity checks in `retrieve.py` and `tests/test_retrieve.py` |
| Tight 6 GB VRAM headroom | Q4_K_M 8B model verified (~20 tok/s); keep retrieved context modest (k=3) |
| No always-on hosting (local LLM, no cloud budget) | Distribute as a one-command local run; optional recorded walkthrough as proof ([ADR-005](./adr/ADR-005-deployment-local-run.md)) |

## 7. Deployment

MockMentor is distributed as a **one-command local run**: clone, run `start.bat`
(it self-bootstraps the venv + dependencies), open `http://localhost:5000`. A
fully-local LLM needs a GPU that free cloud tiers don't provide, and keeping a
personal laptop online continuously isn't practical, so there is no always-on
hosted URL by design. Full reasoning:
[ADR-005](./adr/ADR-005-deployment-local-run.md).

## 8. What shipped vs. the original plan

- **Ahead of plan:** the custom Flask + liquid-glass web app was built during the
  Week 1–2 window, earlier than the original "Week-3 stretch" gate. The earlier
  Streamlit testing UI was later removed once the web app was final.
- **Added:** DSA as a second subject, topic selection with difficulty levels, a
  per-topic weakness report, and a 14-test suite (offline grading-schema tests +
  ChromaDB retrieval integration tests).
- **Settled:** deployment as a local run rather than a tunnel/cloud host, given
  real constraints.
- **Dropped from scope:** wiring user-supplied custom resources into the RAG
  corpus (the UI collects them client-side only; feeding them into retrieval is
  out of scope for this submission).

## 9. References

- [Architecture diagrams](./architecture.md) (C4 L1 + data-flow)
- [ADRs](./adr/) — the individual decisions behind this design
- [README](../README.md) — how to install and run
