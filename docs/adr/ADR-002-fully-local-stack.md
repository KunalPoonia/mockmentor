# ADR-002: Fully local stack (Ollama + local embeddings) over a paid API

**Status:** Accepted
**Date:** 2026-06-27 (model stack chosen during environment setup)

## Context

MockMentor needs two model capabilities: **embeddings** (to turn text into
vectors for retrieval) and a **chat/instruction LLM** (to grade answers and
generate follow-ups). Each can be served either by a hosted API (OpenAI,
Anthropic, Groq, etc.) or by models running locally on the developer's machine.

Constraints and goals shaping the decision:

- **Budget:** a student project with no funding for metered API keys. A grading
  loop that calls an API on every answer accrues per-token cost indefinitely.
- **Privacy:** answers and course material stay on the developer's machine.
- **Learning goal:** the project's stated aim is to understand the *full* RAG
  stack — including inference — not just call someone else's endpoint.
- **Hardware on hand:** 16 GB RAM, RTX 4050 laptop (6 GB VRAM), ~30 GB free
  disk. Enough to run an 8B model at Q4_K_M, but with tight VRAM headroom.

## Decision

Run the entire stack locally:

- **Embeddings:** `all-MiniLM-L6-v2` via `sentence-transformers` (~80 MB, fast
  on CPU, ChromaDB's default) — see `embed_store.py`.
- **Vector store:** ChromaDB, persisted to `chroma_db/` on disk (no server
  process).
- **Grading LLM:** `qwen3:8b` via Ollama, with `llama3.1:8b` kept as a tested
  fallback — see `evaluate.py`.

No API keys, no network dependency at inference time, zero ongoing cost.

## Options considered

- **A — Hosted API for the LLM (rejected).** Higher grading quality (frontier
  models follow "grade only against context" and strict-JSON instructions more
  reliably) and no local hardware limits. Rejected on cost (metered, open-ended)
  and because it defeats the learning goal and the "fully local, private" story.
- **B — Fully local (chosen).** Zero cost, private, offline-capable, and teaches
  the whole stack. Accepts lower model quality and local hardware constraints.
- **C — Hybrid (local dev, hosted small model for the public demo) (deferred).**
  Noted as a possible deployment path but not adopted — it adds complexity and a
  second code path, and a metered key reintroduces the cost risk.

### Why `qwen3:8b` specifically

Started on `llama3.1:8b` (good quality/resource balance, no output quirks).
Switched to `qwen3:8b` for grading because its hybrid "thinking mode" reasons
better about partially-correct answers, and it ran faster on this hardware.
`llama3.1:8b` is retained as a one-argument fallback for when qwen3's `<think>`
output is inconvenient to parse.

## Consequences

**Positive**
- No API cost and no billing risk, ever.
- Works offline; no data leaves the machine.
- Forced genuine understanding of quantization, VRAM budgets, and inference
  behavior (e.g. the qwen3 `<think>` quirk, handled in `evaluate.py`).

**Negative / tradeoffs**
- **Lower grading depth** than a frontier model, especially on ambiguous or
  partially-correct answers. Mitigated by grounded grading (ADR-001), low
  temperature, and a scoped corpus.
- **Local models follow strict-JSON instructions less reliably.** Mitigated
  three ways in `evaluate.py`: `/no_think`, Ollama `format="json"`, and a
  defensive `<think>`-strip + outermost-`{...}` extractor.
- **Deployment is constrained.** A local LLM can't run on free cloud tiers, so
  there's no simple always-on hosted URL. See ADR-005 for how deployment is
  handled given this and the developer's constraints (no funds for a GPU cloud
  VM, laptop not always on).
- **Tight VRAM headroom** (6 GB) caps model size and context length. Verified
  workable (~20 tok/s) but leaves little room; keeping retrieved context modest
  (k=3) is partly a VRAM decision too.

## Related

- ADR-001 (grounding compensates for local-model limits) ·
  ADR-005 (deployment approach forced by running locally).
