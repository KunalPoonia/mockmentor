# ADR-001: Grounded grading — retrieved chunks as ground truth, not the LLM's own judgment

**Status:** Accepted
**Date:** 2026-07-02 (decision made during Step 3.2, `evaluate.py`)

## Context

MockMentor grades a student's spoken-style answer to an interview question. The
central risk for any "AI grades your answer" tool is: **how do you know the
grade is correct?** If the grade rests on a language model's own general
knowledge, then:

- The grade is only as trustworthy as the model's memory, which for an 8B local
  model is limited and can hallucinate.
- The feedback has no traceable connection to what the student actually studied.
- There's no way to show a student *why* an answer was marked wrong beyond "the
  model said so."

For a study tool built on a specific corpus (5 OSTEP chapters, 9 DSA pattern
notes), the answer should be judged against *that material* — the thing the
student is expected to learn — not against the model's unverified opinion.

## Decision

Grade every answer **against retrieved source passages**, not the model's own
knowledge. Concretely:

1. For each question, `retrieve.py` pulls the top-k (k=3) most relevant chunks
   from the subject's ChromaDB collection.
2. `evaluate.py` builds a prompt that includes those chunks as a labelled,
   cited "reference context" block, and the system prompt instructs the model:
   *"Grade ONLY against the provided reference context, not your own outside
   knowledge. If the context does not support a claim, do not credit it."*
3. The returned result carries a `sources` field (the chunks used), so the UI
   can show the exact chapter/page the grade was based on.

This is what makes the system genuinely **Retrieval-Augmented Generation**
rather than an LLM wrapper: retrieval supplies the ground truth, generation only
judges against it.

## Options considered

- **A — LLM judges from its own knowledge (rejected).** Simplest to build (no
  retrieval needed), but fails the core trust requirement: grades are
  ungrounded, unverifiable, and disconnected from the student's material.
- **B — Keyword/rubric matching against a hand-written answer key (rejected).**
  Fully deterministic and explainable, but brittle: it can't handle paraphrase
  or partially-correct answers, and writing rubrics for every question doesn't
  scale.
- **C — Retrieve source passages and have the LLM grade against them (chosen).**
  Combines the LLM's ability to judge nuanced/partial answers with a verifiable
  grounding in real material, and yields citable sources for free.

## Consequences

**Positive**
- Grades and feedback are anchored to real passages and cite chapter/page — the
  student can check the source.
- Reduces (does not eliminate) hallucinated grading, since the model is told to
  judge only against supplied text.
- Generalizes across subjects: any corpus that can be chunked and embedded gets
  grounded grading with no logic change (see ADR-004).

**Negative / tradeoffs**
- Grading quality now depends on **retrieval quality**. If the wrong chunk is
  retrieved, the grade is grounded in the wrong passage. Mitigated by the
  retrieval sanity checks in `retrieve.py` and `tests/test_retrieve.py`.
- The model can still stray from the instruction ("grade only against context")
  — a local 8B model follows this less reliably than a frontier model. Mitigated
  with an explicit system prompt, low temperature (0.2), and a scoped corpus.
- Only content inside the indexed chunks can be graded well; a correct answer
  that draws on material outside the corpus may be under-credited. This is an
  accepted limitation of a deliberately scoped corpus.

## Related

- ADR-002 (why the model is local) · ADR-003 (how chunks are formed) ·
  ADR-004 (how this generalized to a second subject).
