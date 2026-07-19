# ADR-003: Word-based sliding-window chunking (400 words, 50-word overlap)

**Status:** Accepted
**Date:** 2026-06-29 (decided while building `ingest.py`)

## Context

Retrieval works over *chunks* — pieces of the source material small enough to
embed and rank individually. Chunking has two knobs that directly shape
retrieval quality:

- **Chunk size:** too large and a chunk mixes several ideas, so its embedding is
  diffuse and the retrieved passage is padded with irrelevant text (and eats
  VRAM in the grading prompt). Too small and a chunk loses the surrounding
  context needed to actually answer a question.
- **Overlap:** without it, a sentence or idea that straddles a chunk boundary
  gets split across two chunks and may be fully captured by neither.

The corpus is explanatory long-form prose (OSTEP chapters, DSA notes), which
suits medium-sized chunks that each hold roughly one coherent point.

## Decision

Use a **word-based sliding window: 400 words per chunk with 50 words of
overlap** (a 350-word stride), applied uniformly to both ingestion kinds
(`pdf_pages` and `markdown_sections`) in `ingest.py`:

```python
CHUNK_SIZE = 400   # words per chunk
OVERLAP    = 50    # words shared between neighbouring chunks
```

Each OSTEP chunk is tagged with `{chapter_name, page_number}` (page = where the
chunk starts); each DSA chunk with `{chapter_name}` only.

## Options considered

- **Token-based chunking (e.g. 512 tokens / 64 overlap) (rejected for v1).** The
  original plan called for this. Rejected as premature: it needs a tokenizer in
  the ingest path for a benefit that doesn't matter at this corpus size. Word
  count is a good-enough proxy and is trivial to reason about and eyeball.
- **Sentence- or paragraph-boundary chunking (rejected).** Respects semantic
  boundaries better, but is more complex and fragile on PDF-extracted text where
  sentence boundaries are noisy. Deferred as a possible future improvement.
- **No overlap (rejected).** Simpler, but risks losing context at boundaries —
  the exact failure overlap is meant to prevent.
- **Word-based 400/50 sliding window (chosen).** Simple, uniform across both
  corpora, mid-range of the 300–500-word target, and verified to retrieve the
  correct section for known questions.

## Consequences

**Positive**
- Simple and inspectable — `python src/ingest.py <subject>` prints per-section
  chunk counts and previews for eyeballing.
- One chunker serves both PDF and markdown corpora unchanged, which is part of
  why adding DSA was low-touch (ADR-004).
- Verified: OSTEP produces 79 chunks across 5 chapters, and known questions
  retrieve the right section (`tests/test_retrieve.py`).

**Negative / tradeoffs**
- Word count is only an approximation of token count; a chunk's true token
  length varies with vocabulary. Acceptable at this scale and well within the
  embedding model's input limit.
- Fixed-size windows can still cut mid-sentence at the window edge; the 50-word
  overlap softens this but doesn't eliminate it.
- The parameters were chosen from the target range and sanity-checked, not swept
  empirically. If retrieval quality ever degrades, tuning size/overlap is the
  first lever to pull.

### "What would break if I removed the overlap?"

A question whose answer sits right at a chunk boundary could retrieve a chunk
that contains only the first half of the relevant passage (and the second half
lives in the next chunk). The grade would then be grounded in a truncated
passage. The 50-word overlap ensures boundary-straddling context appears in
full in at least one chunk.

## Related

- ADR-001 (chunks are the ground truth grading relies on) ·
  ADR-004 (same chunker reused across subjects).
