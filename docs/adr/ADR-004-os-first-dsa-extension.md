# ADR-004: OS first, DSA as a Week-3 mini-extension

**Status:** Accepted
**Date:** 2026-07 (Week 3, DSA extension)

## Context

The project required a "mini-extension" proving the work generalizes. The
natural candidate was a **second subject** on top of Operating Systems. Two
questions had to be answered: *what* second subject, and *when* to add it.

Key facts shaping the decision:

- OSTEP (the OS corpus) is ready-made, well-structured, long-form explanatory
  prose — an ideal RAG corpus that exists as a single PDF.
- Good DSA teaching material in a RAG-friendly shape did **not** already exist
  in a usable form. Company-tag repositories (e.g.
  `liquidslr/interview-company-wise-problems`) list problem *titles*, not
  explanations — nothing to retrieve against. Usable DSA notes had to be
  authored by hand.
- The real proof point isn't "there are two subjects" — it's that adding the
  second one is **low-touch**, demonstrating the pipeline wasn't hardcoded to OS.

## Decision

**Sequence OS first, add DSA as a scoped Week-3 extension**, and design the
pipeline to be subject-agnostic rather than special-casing OS:

- A per-subject corpus config (`SUBJECT_CORPORA` in `ingest.py`) declares each
  subject's source and how to slice it.
- A second ingestion "kind", `markdown_sections` (DSA notes sliced on `## `
  headers), sits alongside the original `pdf_pages` (OSTEP by page range). Both
  feed the identical downstream pipeline.
- **One ChromaDB collection per subject** (`ostep`, `dsa`), so subjects are
  isolated and adding one can't disturb another.
- `subject` is threaded through `retrieve` / `evaluate` / `server`, and
  `page_number` metadata is made **optional** (OSTEP is paginated; DSA topics
  are cited by name).
- DSA scoped to **9 conceptual pattern topics**, 1–2 paragraphs each, with a
  **conceptual** question bank ("when would you use a sliding window?") rather
  than code-writing — keeping grading tractable for a local model.

## Options considered

- **A — DSA first / instead of OS (rejected).** DSA notes didn't exist and had
  to be written; starting there would have blocked the whole pipeline on content
  authoring before any RAG work could be proven.
- **B — A second textbook PDF as subject #2 (rejected).** Would have reused the
  existing `pdf_pages` path with zero new code — but that proves *less*. Adding
  a *different* source shape (markdown) is stronger evidence of generalization.
- **C — Author scoped DSA markdown notes, add as a Week-3 extension (chosen).**
  Defers content authoring until the pipeline is proven and Python skills are
  stronger, and exercises a genuinely different ingestion path.

## Consequences

**Positive**
- Adding DSA was config + one new ingestion function, not a rewrite — the
  intended proof that the pipeline generalizes.
- No OS regression: OSTEP still ingests to the same 79 chunks and grades/cites
  as before; subjects don't cross-contaminate (separate collections).
- The `markdown_sections` path validates the pipeline against a source shape
  quite different from a paginated PDF.

**Negative / tradeoffs**
- The DSA notes are self-authored and comparatively shallow (1–2 paragraphs per
  topic) — thinner grounding than a full textbook chapter.
- **Academic-integrity flag:** the DSA notes were AI-drafted as a scaffold and
  must be rewritten in the author's own words before submission (noted in the
  file header). The submitted authored content must be the student's own.
- Optional `page_number` metadata adds a small amount of conditional handling
  throughout the pipeline (present for OSTEP, omitted for DSA).

## Related

- ADR-001 (grounded grading applies unchanged to the new subject) ·
  ADR-003 (the same chunker serves both corpora).
