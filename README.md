# MockMentor

AI mock interviewer that grades your answers against real course material and adapts its follow-up questions to what you actually got right or missed.

---

## 1. Demo

> 🚧 **Not yet available.** Demo video and live deployment land in Week 4 (target: 24 July 2026). This section will be updated with a Loom walkthrough and live URL closer to that milestone.

---

## 2. Problem Statement

Most "practice interview" tools either ask static, pre-written questions with no real feedback, or rely on an LLM's own general knowledge to judge whether an answer is correct — which means the grading has no connection to what a student actually studied. MockMentor solves this with Retrieval-Augmented Generation (RAG): every grading decision is grounded in a real passage retrieved from the student's own course material, not the model's unverified opinion. The student answers a question, the system retrieves the relevant textbook chunk, and an LLM grades the answer **against that retrieved passage**, then generates a follow-up question that targets whatever the student's answer didn't cover.

This project is built under **Segment 3 — Foundations of Applied Machine Learning**, problem statement **I2 (Document Q&A / RAG)**, as part of the 2nd Year B.Tech CSE-AIDE Summer Internship (22 June – 26 July 2026).

---

## 3. Architecture

Full diagrams (C4 Level 1 system context + component/data-flow) are in [`docs/architecture.md`](./docs/architecture.md). High-level flow:

```
User Question
     │
     ▼
[Embed Question] ──(sentence-transformers, all-MiniLM-L6-v2)
     │
     ▼
[ChromaDB Retrieval] ──(top-k similarity search over OSTEP chunks)
     │
     ▼
[Retrieved Chunk(s)] + [User's Answer] + [Question]
     │
     ▼
[Local LLM Grading] ──(Qwen3 8B via Ollama)
     │
     ▼
Verdict + Score + Explanation + Model Answer + Sources + Adaptive Follow-up
     │
     ▼
[UI] ──(Flask web app at :5000)
```

---

## 4. Tech Stack

| Component | Choice | Why |
|---|---|---|
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Free, runs locally on CPU/GPU, no API key needed, fast for this corpus size |
| Vector store | ChromaDB | Simple local setup, persists to disk, integrates cleanly with local embeddings |
| LLM (grading + follow-up) | Qwen3 8B, via Ollama | Fully local — zero ongoing cost, offline-capable, fits within 6GB VRAM (RTX 4050) at acceptable speed (~20 tok/s); fallback: Llama 3.1 8B |
| PDF parsing | `pypdf` | Lightweight, sufficient for text-based academic PDFs |
| UI | Flask + static single-page app (liquid-glass design) | Serves the polished interview UI and exposes the RAG pipeline over a small JSON API (`/api/topics`, `/api/question`, `/api/grade`); no browser framework needed |
| Corpus (Subject #1) | *Operating Systems: Three Easy Pieces* (OSTEP), 5 selected chapters | Free, well-structured, long-form explanatory text — well-suited to RAG retrieval; widely used in CS coursework |

Full reasoning for the local-vs-API and model-selection decisions is documented in [ADRs](#8-architecture-decision-records-adrs) (in progress).

---

## 5. Quickstart

### Prerequisites
- Python 3.11+ (developed on 3.12.10)
- [Ollama](https://ollama.com) installed
- ~10 GB free disk space (models + dependencies)
- A GPU is not required, but recommended for reasonable response speed

### Install

```bash
git clone https://github.com/KunalPoonia/mockmentor.git
cd mockmentor

python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

ollama pull qwen3:8b
```

**Source material setup (required, not included in repo):**
The OSTEP textbook PDF is **not committed to this repository** — it's freely available, but redistributing a copy via GitHub isn't appropriate, so it's `.gitignore`'d and must be downloaded separately:

1. Download the book from the official, free source: [pages.cs.wisc.edu/~remzi/OSTEP](https://pages.cs.wisc.edu/~remzi/OSTEP/)
2. Place it at `data/raw/ostep.pdf`

See `data/raw/README.md` for exact instructions.

### Run

> ⚠️ **Activate the venv first.** Every command below must run inside the virtual environment — that's where `chromadb`, `flask`, etc. live. If you run a bare `python` from a plain terminal it uses your *global* Python and fails with `No module named chromadb`.
>
> ```bash
> # Windows:
> .\venv\Scripts\activate
> # macOS/Linux:
> source venv/bin/activate
> ```
> Your prompt should now show `(venv)`. (Or skip activation and call the venv copy directly, e.g. `venv\Scripts\python src/server.py`.)

> **The web app requires Ollama running with `qwen3:8b` and a built `chroma_db/`.** If you haven't embedded the corpus yet, run `python src/embed_store.py` once first (see the data-layer scripts below).

**Web app — the interface (Flask + liquid-glass UI):**
```bash
python src/server.py
```
On Windows you can instead just double-click **`start.bat`** (it uses the venv's Python and starts the server for you).

Then open **http://localhost:5000**. It's a single-page app that walks you through the full flow —

1. **Choose Your Subject** (home page) — Operating Systems and Data Structures & Algorithms are live; others show as *Coming soon*.
2. **Choose a Topic** — a list of the subject's topics, each with a **difficulty badge** (Beginner / Intermediate / Advanced). Pick one to scope the session.
3. **Question** — a question from the chosen topic; type your answer.
4. **Grading** — an animated state while `qwen3:8b` evaluates your response.
5. **Verdict** — colour-coded verdict + score, feedback, a **model answer**, the **sources** the grade was based on, and an adaptive **follow-up** you can answer to continue.
6. **History / Resources** — full pages (not popups). History shows this session's graded answers with stats **and a "Strengths & gaps by topic" weakness report** (per-topic average, sorted weakest-first). Resources shows the corpus (grouped by subject in collapsible dropdowns) plus your own uploaded/linked study material.

Under the hood the server reuses the same pipeline as everything else: `GET /api/topics` and `GET /api/question` serve from `src/questions.py`, and `POST /api/grade` runs `retrieve.py` → `evaluate.py` against the selected subject's collection. Collections are opened once at startup and shared across requests. If Ollama isn't running, the UI shows a clear message instead of failing silently.

**Data-layer scripts (run individually to verify each stage):**
```bash
python src/ingest.py
```
Loads the 5 OSTEP chapters, chunks them, and prints chunk counts + previews for verification. Verified output: 79 chunks across all 5 chapters (Introduction to OS: 23, Scheduling Intro: 14, Address Spaces: 10, Concurrency Intro: 16, Concurrency Problems/Deadlocks: 16), each tagged with `chapter_name` and `page_number` metadata.

```bash
python src/embed_store.py
```
Embeds all chunks and stores them in a local ChromaDB collection (`chroma_db/`). Safe to re-run — recreates the collection cleanly so there are no duplicates.

```bash
python src/retrieve.py
```
Sanity-checks semantic retrieval: runs known questions and confirms they pull back chunks from the correct chapter (top-k=3).

```bash
python src/evaluate.py
```
Runs a demo grade end-to-end (retrieve → grade with `qwen3:8b`) on one sample Q/A, printing the verdict, score, explanation, follow-up, and sources.

### Test

```bash
venv\Scripts\python.exe -m pytest tests -q     # Windows
# or, with the venv active:  pytest -q
```

Two suites (14 tests):
- `tests/test_evaluate.py` — offline unit tests for the grader's output handling: `parse_response` always returns the full JSON schema, coerces the score, strips qwen3 `<think>` blocks, extracts JSON wrapped in prose, and raises on no-JSON; `format_context` includes a page for OSTEP chunks and omits it for DSA. No Ollama needed.
- `tests/test_retrieve.py` — integration tests over the real ChromaDB collections: known OS/DSA questions retrieve the correct section, top-k shape is right, and page metadata is present only for paginated corpora. Requires the stores built (`python src/embed_store.py`); tests **skip** with a clear message if not.

---

## 6. Data Sources

**Subject #1 — Operating Systems:** *Operating Systems: Three Easy Pieces* (OSTEP) by Remzi H. Arpaci-Dusseau and Andrea C. Arpaci-Dusseau. Freely available at [pages.cs.wisc.edu/~remzi/OSTEP](https://pages.cs.wisc.edu/~remzi/OSTEP/). **Not redistributed in this repo** — the PDF is gitignored and must be downloaded separately (see [Quickstart](#5-quickstart)); while OSTEP is free to read, rehosting a copy on GitHub isn't the same as the authors' intended distribution, so this repo links to the source instead. Five chapters selected for this project:

| Chapter | Pages (printed) |
|---|---|
| Introduction to Operating Systems | 24–41 |
| Scheduling: Introduction | 83–94 |
| The Abstraction: Address Spaces | 132–140 |
| Concurrency: An Introduction | 284–298 |
| Common Concurrency Problems (covers deadlocks) | 379–393 |

**Subject #2 — DSA (mini-extension):** Self-authored conceptual notes on 9 common interview patterns (Arrays & Two Pointers, Sliding Window, Binary Search, Linked Lists, Stacks & Queues, Recursion & Backtracking, Trees, Graphs, Dynamic Programming), stored at `data/raw/dsa_notes.md`. Ingested through the **same** pipeline as OSTEP into its own ChromaDB collection, and gradable in the web app. Note: DSA notes are kept as markdown (not PDF like OSTEP) because sections are sliced reliably on `## ` headers — parsing those out of a PDF's extracted text is fragile.

---

## 7. Architecture Decision Records (ADRs)

See [`/docs/adr`](./docs/adr/). Minimum 3 required by Week 4:

- [x] [ADR-001](./docs/adr/ADR-001-grounded-grading.md): Grounded grading (retrieved chunks as ground truth, not the LLM's own judgment)
- [x] [ADR-002](./docs/adr/ADR-002-fully-local-stack.md): Fully local stack (Ollama) over a paid API
- [x] [ADR-003](./docs/adr/ADR-003-chunking-strategy.md): Chunking strategy (window size, overlap)
- [x] [ADR-004](./docs/adr/ADR-004-os-first-dsa-extension.md): OS-first, DSA-as-extension sequencing
- [x] [ADR-005](./docs/adr/ADR-005-deployment-local-run.md): Distribute as a local run, not a hosted deployment

**Design Doc:** [`docs/design_doc.md`](./docs/design_doc.md) — the as-built version, reconciled with what shipped (the original 1-page doc was submitted 24 June per internship requirements).

---

## 8. Mini-Extension

**Done — DSA as a second subject.** Nine interview-pattern topics (self-authored notes) are ingested, embedded, and graded through the exact same `ingest → embed_store → retrieve → evaluate` pipeline as OSTEP, proving the RAG design generalizes beyond a single corpus. Both subjects are selectable and functional in the web app.

**Refactoring effort (the honest signal):** adding DSA was a *light-touch* change, not a rewrite — good evidence the original pipeline was reasonably well-generalized. What changed:

- A small **per-subject corpus config** in `ingest.py` (source path + how to slice it) plus a second ingestion "kind" (`markdown_sections`) alongside the original `pdf_pages`. The existing OSTEP chunking was reused verbatim.
- **One ChromaDB collection per subject** (`ostep`, `dsa`) — the OSTEP collection and its schema were left untouched; each subject queries its own store, so there's no cross-contamination.
- Threaded a `subject` parameter through `retrieve` / `evaluate` / `server` (the grader's interviewer role is now set from the subject name), and made `page_number` **optional** in metadata (OSTEP is paginated; DSA topics are cited by name).
- The UI was already data-driven from `/api/subjects`, so it needed only a `subject` field on the grade request and a page-optional source label — no structural UI change.

**Verified (no regression):** OSTEP still ingests to the same 79 chunks and grades/cites as before; DSA grades sensibly across correct / partially-correct / incorrect answers and cites real DSA topics. Both work in the same running app with no cross-contamination.

**Honest note on academic integrity:** the DSA notes in `data/raw/dsa_notes.md` were AI-drafted as a scaffold and should be rewritten in the author's own words before submission (flagged in the file header) — Doc 01 requires the authored content to be the student's own.

---

## 9. Known Limitations

- Project is in early stages (Week 1 of 5) — most components are still in active development.
- Local LLM (Qwen3 8B) has less reasoning depth than larger hosted models; grading quality on ambiguous or partially-correct answers may be less consistent than a frontier-scale model.
- Corpus is intentionally scoped to 5 chapters of one textbook, not the full subject — by design, to keep retrieval focused and the project deliverable within a 5-week timeline.
- There is no always-on hosted URL. A fully-local LLM needs a GPU (no free cloud tier hosts it) and keeping a personal laptop online 24/7 isn't practical here, so MockMentor is distributed as a **one-command local run** (`start.bat` self-bootstraps the venv + dependencies) rather than a hosted service. A recorded walkthrough can stand in as proof-of-function for anyone who can't run it locally. Full reasoning in [ADR-005](./docs/adr/ADR-005-deployment-local-run.md).

---

## 10. What I'd Do in 3rd Year

See [3rd Year Roadmap](./docs/3rd_year_roadmap.md) *(to be added)*. Early direction: continuous-training/feedback loop, expanded multi-subject corpus, proper eval harness for grading quality, possible session-based weakness tracking across topics.

---

## 11. License & Acknowledgements

License: [MIT](./LICENSE)

Built as part of the 2nd Year B.Tech CSE-AIDE Summer Internship 2026, Segment 3 (Foundations of Applied Machine Learning), under problem statement I2 (Document Q&A / RAG).

Course material: *Operating Systems: Three Easy Pieces* by Remzi H. Arpaci-Dusseau and Andrea C. Arpaci-Dusseau, used under the authors' free-distribution terms for educational purposes.

---

## Project Status (Week 1)

**Segment:** 3 — Foundations of Applied Machine Learning
**Problem Statement:** I2 — Document Q&A (RAG)
**Student:** Kunal Poonia

### What's done
- Environment set up (Python 3.12, venv, all dependencies installed)
- OSTEP corpus confirmed: 5 chapters, exact page ranges identified
- `ingest.py` complete and verified — 79 chunks extracted across all 5 chapters, tagged with chapter name + page metadata
- Local LLM stack chosen and GPU-verified (Qwen3 8B via Ollama, ~20 tok/s on RTX 4050)

### What's in progress
- `embed_store.py` — embedding chunks into ChromaDB

### What's stuck
Nothing is blocking progress right now. The main constraint is hardware — running everything locally on a 6GB VRAM laptop means smaller/slower models than a cloud API would allow, which is a deliberate tradeoff (zero cost, offline-capable) rather than an actual blocker, but it's the thing most likely to need attention if grading quality or response speed becomes an issue in Week 2.

### What I learned this week
- How sliding-window chunking with overlap works in practice (400-word window, 350-word stride = 50-word overlap) and why the overlap matters for not losing context at chunk boundaries.
- The difference between a model's *disk size* and its *VRAM requirement* — learned this the hard way comparing different local LLM options against a 6GB VRAM budget.
- Why grounding LLM grading in retrieved source text (rather than the model's own general knowledge) is what makes a system genuinely "RAG" rather than just an LLM wrapper.
- The difference between a coding assistant running on a subscription (predictable, no surprise bills) versus a metered API key — and why checking which one you're actually authenticated with matters before doing real work.

### 3 goals for next week
1. Complete `embed_store.py` and verify retrieval quality with test queries
2. Build `retrieve.py` and confirm it pulls the correct chapter for sample questions
3. Begin `evaluate.py` — the core grading + follow-up generation logic