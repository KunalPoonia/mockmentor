# MockMentor — Architecture

Two views: a **C4 Level 1 (System Context)** diagram showing MockMentor and the
things around it, and a **component / data-flow** diagram showing what happens
inside when a student submits an answer. Both are Mermaid, so they render
directly on GitHub.

---

## C4 Level 1 — System Context

Who and what MockMentor talks to. Everything runs on the student's own machine
(no cloud, no external APIs) — the only "external" pieces are the local Ollama
runtime and the source material on disk.

```mermaid
flowchart TB
    student["👤 Student<br/><i>practises interview questions</i>"]

    subgraph machine["🖥️ Local machine (no cloud, no API keys)"]
        mm["<b>MockMentor</b><br/>Flask web app + RAG pipeline<br/><i>grades answers against course material,<br/>asks adaptive follow-ups</i>"]
        ollama["<b>Ollama runtime</b><br/><i>serves qwen3:8b locally</i>"]
        corpus[("<b>Source material</b><br/>OSTEP PDF · DSA notes")]
    end

    student -->|"answers questions<br/>in the browser"| mm
    mm -->|"verdict, score, feedback,<br/>model answer, sources, follow-up"| student
    mm -->|"grading prompt<br/>(question + answer + retrieved passages)"| ollama
    ollama -->|"structured JSON grade"| mm
    corpus -.->|"ingested & embedded once<br/>(build step)"| mm
```

---

## Component / Data-flow — grading one answer

What runs inside MockMentor from "student hits Submit" to "verdict on screen".
The dashed path is the one-time **build** step (`embed_store.py`); the solid
path is the **request** flow at grade time.

```mermaid
flowchart TB
    subgraph browser["🌐 Browser — UI/index.html"]
        ui["Single-page app<br/>selector → topic → question →<br/>grading → verdict → follow-up"]
    end

    subgraph server["🐍 Flask — src/server.py"]
        api["JSON API<br/>/api/subjects · /api/topics<br/>/api/question · /api/grade"]
        qbank["questions.py<br/><i>subjects · topics · seed questions</i>"]
    end

    subgraph rag["RAG pipeline (src/)"]
        retrieve["retrieve.py<br/><i>question → top-k chunks</i>"]
        evaluate["evaluate.py<br/><i>grade against chunks<br/>build prompt · parse JSON</i>"]
    end

    subgraph stores["Local models & storage"]
        chroma[("ChromaDB<br/>chroma_db/<br/><i>one collection per subject</i>")]
        embed["all-MiniLM-L6-v2<br/><i>embeddings</i>"]
        llm["qwen3:8b via Ollama<br/><i>grading LLM</i>"]
    end

    ingest["ingest.py<br/><i>PDF / markdown → chunks</i>"]
    raw[("data/raw/<br/>ostep.pdf · dsa_notes.md")]

    %% build-time (one-off)
    raw -.-> ingest -.-> embed -.-> chroma

    %% request-time
    ui -->|"GET question"| api --> qbank
    ui -->|"POST /api/grade<br/>{question, answer, subject}"| api
    api --> retrieve
    retrieve -->|"embed query"| embed
    retrieve -->|"nearest chunks"| chroma
    retrieve -->|"top-k chunks"| evaluate
    evaluate -->|"prompt: grade ONLY<br/>against these chunks"| llm
    llm -->|"JSON verdict"| evaluate
    evaluate -->|"verdict, score, explanation,<br/>model_answer, follow-up, sources"| api
    api -->|"graded result"| ui
```

---

## How to read it

- **The grade is grounded, not guessed.** `retrieve.py` finds the actual source
  passages first; `evaluate.py` tells the model to judge *only* against those.
  That retrieval-before-generation step is what makes this RAG (see
  [ADR-001](./adr/ADR-001-grounded-grading.md)).
- **Everything is local.** Embeddings (`all-MiniLM-L6-v2`), the vector store
  (ChromaDB on disk), and the LLM (`qwen3:8b` via Ollama) all run on the
  student's machine — no external calls (see
  [ADR-002](./adr/ADR-002-fully-local-stack.md)).
- **Build once, then serve.** Ingestion + embedding (dashed path) runs once via
  `python src/embed_store.py`. After that, each answer only walks the solid
  request path.
- **Multi-subject by config.** Each subject has its own ChromaDB collection;
  `ingest.py` slices a PDF by pages or markdown by `## ` headers into the same
  pipeline (see [ADR-004](./adr/ADR-004-os-first-dsa-extension.md)).
