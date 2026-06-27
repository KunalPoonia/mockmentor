# MockMentor — Detailed Build Roadmap

**Project:** AI mock interviewer that grades your answers against real course material (RAG) and adapts its follow-up based on what you got right or missed.
**Segment:** 3 — Foundations of Applied Machine Learning · Problem Statement: I2 (Document Q&A / RAG)
**Stack:** Local embeddings (sentence-transformers) → ChromaDB → fully local LLM (Ollama, Llama 3.1 8B Q4_K_M) → Streamlit
**Hardware:** 16 GB RAM, RTX 4050 Laptop (6 GB VRAM), 30 GB free disk — workable for a 7B model, but tight on VRAM headroom (see Section 1.1)

---

## 0. Before You Write Any Code (Today / Tomorrow)

- [ ] Pick **Subject #1** — the one subject you'll go deep on first. Pick the one where you have the cleanest source material (your own notes, a standard textbook PDF, lecture slides as PDF).
- [ ] Install [Ollama](https://ollama.com) and pull `llama3.1:8b` (Q4_K_M, the default quant Ollama pulls). This is a ~4.5-5 GB download — start it early, don't leave it for the night before a deadline.
- [ ] Run a 5-minute sanity check (see Section 1.1) to confirm the model loads fully on your GPU before building anything on top of it.
- [ ] Repo created on GitHub: **Public**, README on, `.gitignore` → Python. (You've already done this.)
- [ ] Submit the 1-page Design Doc by **24 June, 11:59 PM**.

---

## 1. Environment Setup (Day 5, by 26 June)

```bash
git clone <your-repo-url>
cd mockmentor
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows

pip install chromadb sentence-transformers streamlit pypdf ollama python-dotenv
```

No `.env` / API key needed — everything runs on your own machine.

### 1.1 — GPU Sanity Check (do this BEFORE writing any pipeline code)

Your RTX 4050 has 6 GB VRAM. A 7B model at Q4_K_M needs ~4-5 GB plus 1-2 GB for KV cache/overhead — it fits, but with very little room to spare. Confirm it's actually loading fully on GPU before you build anything on top of it:

```bash
ollama pull llama3.1:8b
ollama run llama3.1:8b "Explain deadlocks in one sentence."
```

While it's running, open a second terminal and check:
```bash
ollama ps
```
This shows what fraction of the model is on GPU vs CPU. You want **100% GPU**. If you see a split (e.g. "48% CPU / 52% GPU"), that means it's spilling into system RAM, and generation will be noticeably slower — closer to the 3-8 tokens/sec CPU range rather than the 30-60 tokens/sec GPU range.

**If it doesn't load 100% on GPU:**
- Close other GPU-using apps (browser with many tabs, especially Chrome — it uses GPU acceleration)
- Try a smaller model as a fallback: `llama3.1:8b` → if too tight, try a 7B alternative like `qwen2.5:7b`, or step down to a 3-4B model (`phi-4-mini` or `llama3.2:3b`) if needed
- Keep your context window modest later (don't send huge retrieved chunks) — context length directly adds to VRAM usage via the KV cache

Don't skip this check — it's the single biggest risk in your stack, and it costs 5 minutes to verify now versus a confusing slowdown to debug in Week 2.

**Folder structure to start with:**
```
mockmentor/
├── data/
│   └── raw/              # your source PDFs/notes go here
├── src/
│   ├── ingest.py         # PDF -> chunks
│   ├── embed_store.py    # chunks -> ChromaDB
│   ├── retrieve.py       # question -> relevant chunks
│   ├── evaluate.py       # answer grading + follow-up generation
│   └── app.py            # Streamlit UI
├── chroma_db/             # ChromaDB's local storage (gitignore this — it's regeneratable)
├── tests/
│   └── test_retrieve.py
├── .gitignore
├── requirements.txt
└── README.md
```

Commit this skeleton today — this is your Day 5 "repo created, environment set up" checkpoint.

---

## 2. Week 1 (29 Jun – 3 Jul): Data Layer

**Goal:** PDF → clean chunks → embedded → stored → basic retrieval works. No UI, no grading logic yet.

### Step 2.1 — Ingest (`ingest.py`)
- Load your Subject #1 PDF using `pypdf`.
- Extract text page by page.
- Chunk it. Start simple: ~300-500 words per chunk, with ~50 word overlap between chunks (overlap prevents losing context at chunk boundaries).
- Keep page numbers as metadata on each chunk — you'll need this later for citing sources.

### Step 2.2 — Embed + Store (`embed_store.py`)
- Use `sentence-transformers` with a small local model (e.g. `all-MiniLM-L6-v2` to start — it's the most battle-tested default, fast on CPU, and is literally ChromaDB's own built-in default).
- Create a ChromaDB collection, add your chunks with their embeddings + metadata (page number, chunk id).
- This only needs to run once per document — cache it, don't re-embed every time you run the app.

### Step 2.3 — Retrieve (`retrieve.py`)
- Write a function: given a question string, embed it with the same model, query ChromaDB for top-k (start with k=3) most similar chunks.
- Print the results to your terminal. Sanity check: does retrieving "What is a deadlock?" actually return the deadlock section of your notes?

### Learning target this week
Be able to explain: *what does chunking do, why did I pick this chunk size, what would break if I removed the overlap?*

### Friday Demo #1 (3 Jul)
Show: PDF in → terminal output of retrieved chunks for a sample question. 3-min explanation of your stack choices.

### Commit checklist for the week
- [ ] At least 5 commits across the week
- [ ] `ingest.py`, `embed_store.py`, `retrieve.py` all working
- [ ] README has a "What is this" + "How to run" section (even rough)

---

## 3. Week 2 (6 Jul – 10 Jul): Core Loop — The "Skinny" Version

**Goal:** The full mechanic works end-to-end, even if ugly. This is your biggest week.

### Step 3.1 — Question bank
- Hand-write 15-20 questions for Subject #1, spanning easy → hard. (Don't auto-generate these yet — having a known, controlled question set makes debugging the grading logic much easier.)

### Step 3.2 — Evaluation logic (`evaluate.py`) — the core of your project
This is the part that makes you legitimately RAG, not just a wrapper around an LLM's opinion. The pattern:

1. User picks/gets a question.
2. Retrieve the top-k relevant chunks for that question (Step 2.3).
3. Build a prompt that gives the LLM: the question, the user's answer, AND the retrieved chunk(s) as the "ground truth" reference.
4. Ask the LLM to:
   - Grade the answer (correct / partially correct / incorrect) **based on the retrieved material, not its own general knowledge**
   - Explain briefly why
   - Generate ONE follow-up question that is *adaptive*, not just "harder":
     - If correct → a deeper or adjacent concept from the same retrieved material
     - If partially correct → a follow-up targeting the specific gap
     - If incorrect → a clarifying question or a "did you mean X" nudge

**Prompt design tip:** Ask the LLM to return structured output (e.g. a JSON object with `verdict`, `explanation`, `follow_up_question`) so your code can parse it reliably instead of trying to regex free text. Local models follow strict JSON instructions less reliably than Claude/GPT-tier models — explicitly tell it "respond with ONLY valid JSON, no other text" and add a fallback parse step in case it adds stray text around the JSON.

**Calling your local model from Python** (via the `ollama` library):
```python
import ollama

response = ollama.chat(
    model='llama3.1:8b',
    messages=[{'role': 'user', 'content': your_prompt}]
)
print(response['message']['content'])
```
Keep `ollama serve` running in the background (it usually auto-starts after install) while you develop.

### Step 3.3 — Wire it together (`app.py`, basic Streamlit)
- Text input for the user's answer
- Button: "Submit"
- Display: verdict, explanation, follow-up question
- This does not need to be pretty yet.

### Mid-program mentor 1:1 (Wed this week)
Bring two things: *"Is grounding the grading in retrieved chunks, instead of the LLM's own judgment, the right way to avoid the 'how do you know the answer is correct' problem?"* (your strongest design decision), and *"I'm running a local 7B model on a 6GB-VRAM laptop instead of an API — here's how I'm handling cases where it gives inconsistent grading."* Mentors will likely find the local-first approach a genuinely interesting technical choice — be ready to explain why you chose it (cost, privacy, offline capability, "I wanted to understand the full stack including inference, not just call an API").

### Friday Demo #2 (10 Jul)
End-to-end: pick a question → answer it → see verdict + follow-up. Ugly UI is fine.

### Commit checklist
- [ ] `evaluate.py` working with structured LLM output
- [ ] Basic Streamlit app runs locally
- [ ] 1-paragraph ADR note: "why grounded grading instead of free LLM judgment"

---

## 4. Week 3 (13 Jul – 17 Jul): Polish + Mini-Extension

**Goal:** Make it presentable. Add your mini-extension.

### Step 4.1 — Polish
- Clean up the Streamlit UI: maybe a progress indicator, a "weakness report" summary screen at the end of a session (this ties back to your original pitch — tracks which topics the user got wrong across a session and summarizes it)
- Add 1-2 tests (e.g. test that retrieval returns non-empty results for a known question; test that the evaluate function returns valid structured output)
- README polish: clear "what/why/how/how-to-run"

### Step 4.2 — Mini-Extension (pick one, or both if time allows)
**Option A — Add Subject #2:** Repeat Steps 2.1-2.3 for a second subject (e.g. DSA). This proves your pipeline generalizes, not just works for one hardcoded case. Cleanest, lowest-risk extension.

**Option B — Session weakness report:** Track every question asked + verdict across a session, and at the end generate a summary: "You're strong on X, weak on Y, here's what to review." This was literally your original pitch — building it out properly as the extension is a strong, coherent story.

**Recommendation:** Given your timeline and that you're still building Python fluency, Option A is the safer bet to *guarantee* you finish; Option B is the more impressive one if Weeks 1-2 go smoothly. Decide based on how Week 2 actually goes — don't commit now.

### Friday Demo #3 (17 Jul)
Polished version + mini-extension demoed.

---

## 5. Week 4 (20 Jul – 24 Jul): Deploy + Document

**Goal:** Live URL. Full documentation.

### Step 5.1 — Deploy

**Important constraint:** Streamlit Community Cloud (and most free-tier clouds) can't run Ollama — they don't give you a GPU or let you install/run a local model server. A fully local LLM, almost by definition, runs on *your* machine, not a free cloud host. This needs a different deploy strategy than the API version would have:

**Option A (recommended — satisfies the "live URL" requirement honestly):** Deploy the Streamlit app on **your own machine**, and expose it publicly using a tunnel:
- Run your Streamlit app locally (`streamlit run app.py`)
- Use a free tunnel tool like **ngrok** or **Cloudflare Tunnel** to get a public URL pointing at your local machine
- Doc 01 explicitly allows this: *"local + public tunnel"* is named as an acceptable deployment path
- Caveat: the link only works while your laptop is on and the app is running — fine for demo day, but mention this clearly in your README so it's not mistaken for an always-on deployment

**Option B (more "really deployed," more setup):** Deploy on a cloud VM with a GPU:
- Some free-tier cloud credits (e.g. a student GCP/AWS credit) can run a small VM, but a 7B model still needs a GPU instance, which usually isn't covered by free tiers — likely to cost real money or hit quota limits
- Not recommended given your timeline; Option A is the standard, accepted approach for local-LLM student projects

**Option C (hybrid, if you want a true always-on URL):** Keep Ollama local for development/demo, but for the *deployed* version, swap in a free-tier hosted small model (e.g. via Hugging Face Inference or a free tier of Groq) just for the public deployment, while your README/ADR clearly explains your local-first development approach and why the deployed version differs. More complex — only attempt if Weeks 1-3 go smoothly.

**Recommendation:** Go with **Option A**. It satisfies every Doc 01 requirement, keeps your "fully local, zero API cost" story intact, and is the lowest-risk path given your timeline.

### Step 5.2 — Documentation
- **README final**: what it is, why you built it, how the RAG grading works, how to run it locally (including the Ollama install step), how to access the demo (tunnel link + note that it requires your machine to be running), link to the Loom as a backup if the tunnel is ever down.
- **3 ADRs minimum** — you already have one from Week 2 (grounded grading). Add two more, e.g.: "why fully local (Ollama) over an API," "why this chunk size/overlap." The local-vs-API ADR is a strong one — you have a genuinely well-reasoned answer from working through this trade-off.
- **3-min Loom**: record this regardless of Option A/B/C — it's your safety net if the live tunnel link ever isn't working when someone checks it later.
- **Reflection piece (1000-1500 words)**: what you learned, what you'd do differently, what's next. (Save real time for this — it's graded under Communication.)

### Friday Demo #4 (24 Jul)
Live deployment demo + walkthrough.

---

## 6. Week 5 (25-26 Jul): Submit + Showcase

- **25 Jul:** Final submission — repo, live URL, README, Loom, reflection, resume bullets.
- **26 Jul:** Public showcase, 5 min presentation.

---

## 7. Things to Watch Out For

| Risk | Mitigation |
|---|---|
| Spending too long perfecting chunking in Week 1 | Time-box it. A working "good enough" chunker beats a perfect one you're still tuning in Week 2. |
| Local model spills to CPU, runs slowly | Run the GPU sanity check in Section 1.1 *before* building. Keep context windows modest. Have a smaller fallback model (3-4B) ready if needed. |
| Local 7B model gives inconsistent/hallucinated grading despite retrieval | Make the prompt explicit: "Only use the provided reference material to judge correctness. If the reference doesn't cover this, say so." Test with your hand-written question bank early and tune the prompt before building the UI on top of it. |
| Python unfamiliarity slows Week 2 | This is your highest-risk week. Don't be afraid to ask in Slack #help or office hours (Wed/Fri 4-6 PM) early, not after being stuck for days. |
| Scope creep (multiple subjects too early) | Stick to one subject deep until Week 3. Resist adding more until the core loop is solid. |
| Tunnel link down during evaluation/showcase | Keep the Loom video as backup proof it works. Test the tunnel the morning of each demo day, not the night before. |
| Forgetting the "push every day" pledge | Even a README tweak counts. Don't let the graph go cold. |

---

## 8. Your Resume Bullet (Draft Now, Refine Later)

*"Built MockMentor, a fully local RAG-based AI mock interview tool that retrieves relevant course material to ground answer evaluation and generate adaptive follow-up questions, using ChromaDB, sentence-transformers, and a locally-hosted Llama 3.1 8B model via Ollama — zero API cost, fully offline-capable."*

You'll tighten this after you've actually built it — but having a draft now keeps the "why am I building this" framing honest throughout.