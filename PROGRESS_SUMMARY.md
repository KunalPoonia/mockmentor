# MockMentor - Complete Progress Summary
it's a personal/supplementary log, not the official status doc
**Last Updated:** June 29, 2026

---

## 📖 Complete Story: From Zero to Ready for Development

### **What We Built**
MockMentor is an AI-powered mock interview tool that:
- Uses RAG (Retrieval-Augmented Generation) to ground answers in actual course material
- Grades student responses based on retrieved content (not just LLM general knowledge)
- Generates adaptive follow-up questions based on performance
- Runs 100% locally with zero API costs

**Target Subject:** Operating Systems (using OSTEP textbook)

---

## ✅ Phase 1: Environment & Foundation (COMPLETE)

### **1.1 - LLM Setup & GPU Verification**

**What we did:**
- Installed Ollama for local LLM inference
- Pulled and tested `llama3.1:8b` (Q4_K_M quantization, 4.9 GB)
- **GPU sanity check passed:**
  - **75% GPU utilization** (CUDA-accelerated inference)
  - **25% CPU utilization** (model loading/preprocessing)
  - **~20 tokens/second** generation speed
  - Verified with multi-turn conversation test

**Why this matters:** Confirmed your hardware can handle real-time inference for the mock interview app without freezing or lag.

**Models now available:**
```
qwen3:8b      (5.2 GB) - Primary model for MockMentor (hybrid thinking mode)
llama3.1:8b   (4.9 GB) - Tested fallback (no <think> quirk)
qwen2.5:7b    (4.7 GB) - Alternative (if needed)
```

---

### **1.2 - Project Structure & Git Setup**

**Repository created:** `github.com/KunalPoonia/mockmentor`

**Directory structure:**
```
mockmentor/
├── .git/                   # Version control initialized
├── venv/                   # Python 3.12.10 virtual environment
├── data/
│   └── raw/
│       ├── ostep.pdf       # OSTEP textbook (675 pages, verified readable)
│       └── README.md       # Download instructions for future users
├── src/                    # Application modules (placeholders ready)
│   ├── ingest.py           # PDF → text chunks
│   ├── embed_store.py      # Chunks → ChromaDB
│   ├── retrieve.py         # Question → relevant chunks
│   ├── evaluate.py         # Grading + follow-up logic
│   └── app.py              # Streamlit UI
├── tests/                  # Test directory (ready for use)
├── chroma_db/              # Vector DB (gitignored, will be created in Step 2)
├── .gitignore              # Configured properly
├── requirements.txt        # Dependencies defined
└── README.md               # Full project documentation
```

---

### **1.3 - Python Environment & Dependencies**

**Virtual environment:** Python 3.12.10 (activated in `venv/`)

**Installed packages (verified working):**
```
chromadb          1.5.9   # Vector database for RAG
sentence-transformers 5.6.0  # Embedding model
streamlit         1.58.0  # Web UI framework
pypdf             6.14.2  # PDF text extraction
ollama            0.6.2   # Python client for Ollama
torch             2.12.1  # PyTorch (for sentence-transformers)
numpy             2.5.x   # Numerical operations
```

**Status:** All packages import successfully, no conflicts.

---

### **1.4 - Source Material (OSTEP Textbook)**

**File:** `data/raw/ostep.pdf`
- **Pages:** 675 (verified)
- **Readable:** ✓ (tested with pypdf extraction on Ch 2)
- **Target chapters for RAG corpus:**
  1. Ch 02: Introduction to Operating Systems (pp. 24-41)
  2. Ch 07: Scheduling Introduction (pp. 83-94)
  3. Ch 13: Address Spaces (pp. 132-140)
  4. Ch 26: Concurrency Introduction (pp. 284-298)
  5. Ch 32: Concurrency Problems/Deadlocks (pp. 379-393)

**Decision made:** PDF is gitignored (not committed to repo) to respect copyright. README contains download instructions for future users.

---

### **1.5 - Git History & Commits**

**Commit history (latest to oldest):**
```
fa4cbec - docs: remove roadmap from repo (keeping as personal planning doc)
07c9e0e - fix: remove PDF from repo, add download instructions to respect copyright
14fedf9 - env: set up virtual environment with dependencies and add OSTEP source PDF (675 pages)
35a0a39 - feat: initial project structure with folders, requirements, and placeholder modules
9462a9d - docs: add detailed build roadmap with OSTEP corpus and DSA extension plan
```

**Current status:**
- Branch: `main`
- Remote: `origin/main` (GitHub)
- Working tree: **clean** (no uncommitted changes)

---

### **1.6 - Documentation**

**README.md** includes:
- Project description and goals
- Tech stack explanation
- Installation instructions (with Ollama setup)
- Download instructions for OSTEP
- Project structure overview
- Current status checklist

**.gitignore** properly excludes:
- `venv/` (virtual environment)
- `chroma_db/` (vector database, will be regenerated)
- `data/raw/*.pdf` (copyrighted source material)
- Python cache, IDE files, logs

**data/raw/README.md** explains:
- Where to download OSTEP
- Expected file format (675 pages)
- Target chapters for this project

---

## 🎯 Current Status: Step 2.1 Complete — Building the Data Layer

### **What's Working:**
✅ Local LLM inference (Ollama + qwen3:8b, llama3.1:8b fallback)  
✅ GPU acceleration confirmed (~20 tok/s)  
✅ Python environment with all dependencies  
✅ Git repo initialized and pushed to GitHub  
✅ OSTEP PDF downloaded and verified readable  
✅ Project structure and documentation complete  
✅ **`src/ingest.py` built & verified — 79 chunks across 5 chapters**  

### **What's Next (Step 2.2 - Embed & Store):**
⏳ Embed the 79 chunks with `all-MiniLM-L6-v2` (sentence-transformers)  
⏳ Store embeddings + metadata in a ChromaDB collection  
⏳ Then Step 2.3 — retrieval sanity check against the 5 chapters  

---

## 🔍 Technical Decisions Made

### **1. Why fully local?**
- Zero API costs (no OpenAI/Anthropic bills)
- Complete privacy (no data sent to third parties)
- Offline capability (no internet dependency)
- Learning opportunity (understanding the full RAG stack)

### **2. Why Qwen3 8B (switched from Llama 3.1 8B)?**
- Started on `llama3.1:8b` — good quality/resource balance, 8B fits consumer GPU, Q4_K_M keeps it ~4.9 GB
- **Switched to `qwen3:8b`** for the grading task: its hybrid "thinking mode" helps reason about partially-correct answers, and it ran faster on this hardware
- `llama3.1:8b` kept as a tested fallback — no `<think>` tag quirk, so it's the safety net if Qwen3's output proves fussy to parse in `evaluate.py`
- Both are Q4_K_M quantized (~4.9–5.2 GB), strong instruction-following for grading/evaluation

### **3. Why ChromaDB?**
- Lightweight, embedded vector database
- No separate server process needed
- Built-in support for sentence-transformers embeddings
- Easy persistence to disk

### **4. Why sentence-transformers (all-MiniLM-L6-v2)?**
- Small model (80 MB) that runs fast on CPU
- Decent semantic similarity for educational content
- No GPU required for embedding (saves memory for LLM)
- Standard choice for local RAG projects

### **5. Why Streamlit?**
- Rapid prototyping (no HTML/CSS/JS needed)
- Built-in session state for conversation history
- Easy deployment (one command: `streamlit run app.py`)
- Good enough for local/demo use (not production-scale)

---

## 📊 Metrics & Verification Results

### **PDF Verification:**
```python
✓ PDF loaded: 675 pages
✓ Text extraction working (tested on Ch 2, page 24)
✓ Sample output: "Introduction to Operating Systems..."
```

### **Package Import Test:**
```python
✓ Python 3.12.10
✓ chromadb, sentence_transformers, streamlit, pypdf, ollama
✓ All core packages imported successfully
```

### **Ollama Models:**
```
llama3.1:8b   (46e0c10c039e) - 4.9 GB - 36 hours ago
qwen2.5:7b    (845dbda0ea48) - 4.7 GB - 8 minutes ago
qwen3:8b      (500a1f067a9f) - 5.2 GB - 4 minutes ago
```

### **GPU Utilization (Llama 3.1 8B):**
- **GPU:** 75% (CUDA inference on NVIDIA GPU)
- **CPU:** 25% (preprocessing, tokenization)
- **Speed:** ~20 tokens/second (interactive speed)

---

## 🛠️ Refinements & Fixes Applied

### **Issue 1: Commit message overclaim**
**Problem:** Commit said "add OSTEP corpus (675 pages, 5 chapters)" but only the raw PDF was added, not the processed corpus.

**Fix applied:**
```bash
# Amended commit message to:
"env: set up virtual environment with dependencies and add OSTEP source PDF (675 pages)"
```

**Lesson:** Precision in commit messages matters for portfolio/communication grading.

---

### **Issue 2: Committing the OSTEP PDF**
**Problem:** The 675-page OSTEP PDF was initially committed to the repo. While OSTEP is freely distributed, redistributing via GitHub wasn't ideal.

**Fix applied:**
```bash
# Removed PDF from repo, added to .gitignore
# Added download instructions to README
```

**Why this matters:**
- Standard practice in student repos (don't rehost textbooks)
- Keeps repo size small
- Shows understanding of copyright etiquette

---

### **Issue 3: .gitignore completeness**
**Verified excluded:**
- `venv/` (never commit virtual environments)
- `chroma_db/` (regeneratable vector database)
- `data/raw/*.pdf` (source material, download separately)
- `__pycache__/`, `.pyc` files (Python cache)

**Status:** Clean `.gitignore` verified in commit 07c9e0e

---

## 📝 Lessons Learned

1. **GPU sanity checks catch problems early:** Verifying 75% GPU utilization upfront means no surprises when building the full app.

2. **Commit message precision matters:** "Add source PDF" ≠ "Add processed corpus." Small wording issues compound in project history.

3. **Gitignore first, commit second:** Setting up `.gitignore` before committing the PDF would've avoided the "remove PDF" commit.

4. **Copyright respect ≠ paranoia:** OSTEP is freely available, but best practice = link to source, don't rehost. Shows professional judgment.

5. **Virtual environment hygiene:** Committing `venv/` is the #1 beginner mistake. We avoided it by setting up `.gitignore` correctly.

---

## 🎓 Educational Value

This project demonstrates:
- **RAG system architecture** (retrieval → augmentation → generation)
- **Local LLM deployment** (Ollama, quantization, GPU inference)
- **Vector similarity search** (embeddings → ChromaDB → retrieval)
- **Evaluation logic** (comparing student answers to ground truth)
- **Full-stack ML** (data → model → UI → deployment)

Built for **Foundations of Applied Machine Learning** (Segment 3, Problem I2: Document Q&A / RAG).

---

## 🚀 Next Steps (Week 1 - Data Layer)

### **Step 2.1 - Extract & Chunk OSTEP Chapters** ✅ DONE (Jun 29)
**Goal:** Convert 5 target chapters into overlapping text chunks tagged with metadata.

**What was built:**
- [x] `src/ingest.py`:
  - Page-range extraction for all 5 chapters (0-indexed pypdf pages)
  - Word-based chunking: ~400 words/chunk with 50-word overlap
  - Each chunk tagged with `chapter_name` + `page_number` metadata
  - `get_chunks()` returns the chunks in-memory (no JSON file — `embed_store.py` imports it directly)
- [x] Verified: **79 chunks** (Intro 23, Scheduling 14, Address Spaces 10, Concurrency Intro 16, Concurrency Problems 16)

**Note on the spec change:** the original plan said "512 tokens / 64 overlap" saved to `chunks.json`. The actual build uses **word-based** chunking (~400 words / 50 overlap, matching the roadmap's 300-500 word target) and returns chunks **in-memory** rather than persisting JSON — simpler for a first pass and avoids a redundant on-disk format before embedding.

**Actual chunk shape:**
```python
{
    "text": "Introduction to Operating Systems...",
    "chapter_name": "Introduction to OS",
    "page_number": 23,
}
```

---

### **Step 2.2 - Embed & Store in ChromaDB**
**Goal:** Convert text chunks → embeddings → store in ChromaDB for retrieval.

**Implementation checklist:**
- [ ] Write `src/embed_store.py`:
  - Load `sentence-transformers` model (`all-MiniLM-L6-v2`)
  - Generate embeddings for all chunks
  - Initialize ChromaDB collection
  - Store embeddings with metadata
- [ ] Verify `chroma_db/` directory created
- [ ] Test retrieval with sample query (e.g., "What is a process?")

**Testing criteria:**
```python
# Should retrieve relevant chunks:
query = "What is a process?"
results = collection.query(query_texts=[query], n_results=3)
# Expected: chunks from Ch 2 (Intro to OS)
```

---

## 📈 Progress Timeline

| Date | Milestone | Status |
|------|-----------|--------|
| Jun 26 | Install Ollama, pull llama3.1:8b | ✅ Done |
| Jun 26 | GPU sanity check (75% GPU, 20 tok/s) | ✅ Done |
| Jun 27 | Create project structure | ✅ Done |
| Jun 27 | Set up Python venv + install deps | ✅ Done |
| Jun 27 | Download & verify OSTEP PDF (675 pages) | ✅ Done |
| Jun 27 | Git init, push to GitHub | ✅ Done |
| Jun 27 | Fix commit message precision | ✅ Done |
| Jun 27 | Remove PDF from repo, update .gitignore | ✅ Done |
| Jun 27 | Remove roadmap from repo (keep local) | ✅ Done |
| Jun 27 | Pull qwen3:8b, switch to it as primary | ✅ Done |
| Jun 29 | Build & verify `ingest.py` (79 chunks, 5 chapters) | ✅ Done |
| **Next** | **Embed & store chunks in ChromaDB** | ⏳ Pending |
| **Next** | **Retrieval sanity check (Step 2.3)** | ⏳ Pending |

---

## 🎯 Deliverables Checklist (Week 0-1)

- [x] Ollama installed, model pulled (llama3.1:8b)
- [x] GPU sanity check complete (75% GPU / 25% CPU, ~20 tok/s)
- [x] Project repository created on GitHub
- [x] Project structure with placeholder modules
- [x] Virtual environment with all dependencies installed
- [x] OSTEP PDF downloaded and verified (675 pages, readable)
- [x] README.md with installation and usage instructions
- [x] .gitignore properly configured
- [x] Clean git history (no bloat, clear commit messages)
- [x] Data ingestion pipeline (`src/ingest.py`) — 79 chunks, verified
- [ ] Embedding & storage pipeline (`src/embed_store.py`)
- [ ] Retrieval logic (`src/retrieve.py`)
- [ ] Grading logic (`src/evaluate.py`)
- [ ] Streamlit UI (`src/app.py`)

**Phase 1 completion:** 10/14 items (71%)  
**Phase 2 readiness:** 100% (all prerequisites met)

---

## 💡 Key Takeaways

1. **Foundation work is invisible but critical:** Setting up GPU acceleration, virtual environments, and .gitignore correctly saves hours of debugging later.

2. **Commit hygiene matters from day 1:** Amending commit messages and removing accidentally-committed files is friction that good `.gitignore` setup avoids.

3. **Verification at every step:** Testing PDF readability, GPU utilization, and package imports before moving forward prevents "it works on my machine" surprises.

4. **Documentation = communication:** Clear README + inline commit messages = easier to explain this project in interviews or code reviews.

5. **Local-first = constraints + learning:** Zero API costs is great, but you need to understand quantization, GPU memory, and inference speed to make it work.

---

## 📞 Contact & Repository

**Author:** Kunal Poonia  
**GitHub:** [github.com/KunalPoonia/mockmentor](https://github.com/KunalPoonia/mockmentor)  
**License:** MIT  

**Course Context:** Foundations of Applied Machine Learning (Segment 3, Problem I2: Document Q&A / RAG)

---

**End of Progress Summary**  
*Step 2.1 (Data Ingestion) complete — ready to begin Step 2.2 (Embed & Store) whenever you are.*
