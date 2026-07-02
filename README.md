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

> 🚧 **Diagram pending.** A C4 Level 1 architecture diagram will be added to `/docs` once the core pipeline (Weeks 1-2) is complete. High-level flow in the meantime:

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
[UI] ──(Flask web app at :5000, or Streamlit for testing)
```

---

## 4. Tech Stack

| Component | Choice | Why |
|---|---|---|
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Free, runs locally on CPU/GPU, no API key needed, fast for this corpus size |
| Vector store | ChromaDB | Simple local setup, persists to disk, integrates cleanly with local embeddings |
| LLM (grading + follow-up) | Qwen3 8B, via Ollama | Fully local — zero ongoing cost, offline-capable, fits within 6GB VRAM (RTX 4050) at acceptable speed (~20 tok/s); fallback: Llama 3.1 8B |
| PDF parsing | `pypdf` | Lightweight, sufficient for text-based academic PDFs |
| UI (main) | Flask + static single-page app (liquid-glass design) | Serves the polished interview UI and exposes the RAG pipeline over a small JSON API (`/api/question`, `/api/grade`); no browser framework needed |
| UI (testing) | Streamlit | Fastest path to a working interactive app for quick pipeline iteration |
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

> ⚠️ **Activate the venv first.** Every command below must run inside the virtual environment — that's where `chromadb`, `streamlit`, etc. live. If you run a bare `streamlit`/`python` from a plain terminal it uses your *global* Python and fails with `No module named chromadb`.
>
> ```bash
> # Windows:
> .\venv\Scripts\activate
> # macOS/Linux:
> source venv/bin/activate
> ```
> Your prompt should now show `(venv)`. (Or skip activation and call the venv copy directly, e.g. `venv\Scripts\streamlit run src/app.py`.)

> **Both UIs require Ollama running with `qwen3:8b` and a built `chroma_db/`.** If you haven't embedded the corpus yet, run `python src/embed_store.py` once first (see the data-layer scripts below).

**Web app — the main interface (Flask + liquid-glass UI):**
```bash
python src/server.py
```
Then open **http://localhost:5000**. This is the primary front end: a single-page app that walks you through the full flow —

1. **Choose Your Subject** (home page) — Operating Systems is live; other subjects show as *Coming soon*.
2. **Question** — a question from the OSTEP-backed bank (10 per session); type your answer.
3. **Grading** — an animated state while `qwen3:8b` evaluates your response.
4. **Verdict** — colour-coded verdict + score, feedback, a **model answer**, the OSTEP **sources** the grade was based on, and an adaptive **follow-up** you can answer to continue the session.

Under the hood the server reuses the same pipeline as everything else: `GET /api/question` serves questions from `src/questions.py`, and `POST /api/grade` runs `retrieve.py` → `evaluate.py`. The ChromaDB collection is opened once at startup and shared across requests. If Ollama isn't running, the UI shows a clear message instead of failing silently.

**Streamlit app — lightweight testing UI:**
```bash
streamlit run src/app.py
```
A simpler interface for quick iteration on the pipeline: pick a chapter + question, submit an answer, and see the same RAG-grounded grade (verdict, score, feedback, model answer, follow-up, sources). Handy when you want to test grading changes without the full web front end.

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

> 🚧 Tests are planned for Week 3, per the project scope (1-2 tests is the internship standard for this level). `tests/` directory is scaffolded.

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

**Subject #2 — DSA (mini-extension, Week 3):** Self-authored conceptual notes on 8-10 common interview patterns (Arrays, Two Pointers, Sliding Window, etc.), with topic selection informed by company-tag frequency data from public interview-question repositories. Not yet written — planned for Week 3.

---

## 7. Architecture Decision Records (ADRs)

See [`/docs/adr`](./docs/adr/). Minimum 3 required by Week 4; in progress:

- [ ] ADR-001: Grounded grading (retrieved chunks as ground truth, not the LLM's own judgment)
- [ ] ADR-002: Fully local stack (Ollama) over a paid API
- [ ] ADR-003: Chunking strategy (window size, overlap)
- [ ] ADR-004 *(optional)*: OS-first, DSA-as-extension sequencing

**Design Doc:** Not yet added to the repo. Original 1-page design doc was submitted 24 June per internship requirements; the final version (post mentor review) will be added at `docs/design_doc.md` before Week 1 submission.

---

## 8. Mini-Extension

**Planned (Week 3):** Add DSA as a second subject, proving the RAG pipeline generalizes beyond a single corpus. Conceptual notes on 8-10 high-frequency interview topics will be authored, ingested through the same pipeline, and graded the same way as OS content. Not yet implemented.

---

## 9. Known Limitations

- Project is in early stages (Week 1 of 5) — most components are still in active development.
- Local LLM (Qwen3 8B) has less reasoning depth than larger hosted models; grading quality on ambiguous or partially-correct answers may be less consistent than a frontier-scale model.
- Corpus is intentionally scoped to 5 chapters of one textbook, not the full subject — by design, to keep retrieval focused and the project deliverable within a 5-week timeline.
- Live deployment will run via a local-machine + tunnel setup (ngrok/Cloudflare Tunnel), not an always-on cloud host — the link will only be reachable while the developer's machine is running. Documented as an accepted deployment path for fully-local LLM projects in this internship's workflow guide.

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