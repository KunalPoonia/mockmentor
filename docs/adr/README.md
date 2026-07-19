# Architecture Decision Records (ADRs)

This folder records the significant technical decisions behind MockMentor —
the context each decision was made in, the options considered, what was chosen,
and the tradeoffs that came with it. The goal is to make the reasoning behind
the design explicit and reviewable, not just the final code.

Each ADR is a short, standalone document. Status values: **Accepted** (in
effect), **Superseded** (replaced by a later ADR), **Proposed** (under
discussion).

| ADR | Title | Status |
|---|---|---|
| [ADR-001](./ADR-001-grounded-grading.md) | Grounded grading: retrieved chunks as ground truth, not the LLM's own judgment | Accepted |
| [ADR-002](./ADR-002-fully-local-stack.md) | Fully local stack (Ollama + local embeddings) over a paid API | Accepted |
| [ADR-003](./ADR-003-chunking-strategy.md) | Word-based sliding-window chunking (400 words, 50 overlap) | Accepted |
| [ADR-004](./ADR-004-os-first-dsa-extension.md) | OS first, DSA as a Week-3 mini-extension | Accepted |
| [ADR-005](./ADR-005-deployment-local-run.md) | Distribute as a local run, not a hosted deployment | Accepted |
