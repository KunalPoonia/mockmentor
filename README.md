# MockMentor

**AI mock interviewer that grades your answers against real course material (RAG) and adapts its follow-up based on what you got right or missed.**

## 🎯 What is this?

MockMentor is a fully local RAG-based AI mock interview tool that:
- Retrieves relevant course material from your notes/textbooks
- Grounds answer evaluation in retrieved content (not just LLM's general knowledge)
- Generates adaptive follow-up questions based on your performance
- Runs 100% locally with zero API costs

## 📚 Coverage

- **Operating Systems** - Using OSTEP (Operating Systems: Three Easy Pieces)
- **Data Structures & Algorithms** - Pattern-focused conceptual explanations

## 🛠️ Tech Stack

- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector Store:** ChromaDB
- **LLM:** Ollama (Llama 3.1 8B, Q4_K_M quantization)
- **UI:** Streamlit
- **Corpus Processing:** pypdf

## 🚀 Getting Started

### Prerequisites

1. **Install Ollama** from [ollama.com](https://ollama.com)
2. **Pull the model:**
   ```bash
   ollama pull llama3.1:8b
   ```

### Installation

```bash
# Clone the repository
git clone https://github.com/KunalPoonia/mockmentor.git
cd mockmentor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
# Make sure Ollama is running (usually auto-starts)
# Then run the Streamlit app
streamlit run src/app.py
```

## 📂 Project Structure

```
mockmentor/
├── data/
│   └── raw/              # Source PDFs/notes
├── src/
│   ├── ingest.py         # PDF → chunks
│   ├── embed_store.py    # Chunks → ChromaDB
│   ├── retrieve.py       # Question → relevant chunks
│   ├── evaluate.py       # Answer grading + follow-up generation
│   └── app.py            # Streamlit UI
├── chroma_db/            # Vector database (gitignored)
├── tests/                # Test files
├── requirements.txt
├── .gitignore
└── README.md
```

## 📋 Status

**Current Phase:** Environment Setup (Week 0-1)

- [x] Ollama installed, model pulled (Llama 3.1 8B)
- [x] GPU sanity check complete (75% GPU / 25% CPU, ~20 tok/s)
- [x] Project structure created
- [ ] Data ingestion pipeline
- [ ] Embedding & retrieval system
- [ ] Grading logic
- [ ] Streamlit UI

See [ROADMAP.md](ROADMAP.md) for detailed build plan.

## 🎓 Educational Context

Built as part of Foundations of Applied Machine Learning (Segment 3, Problem I2: Document Q&A / RAG).

**Why fully local?**
- Zero API costs
- Complete privacy
- Offline capability
- Understanding the full inference stack

## 📝 License

MIT License - see LICENSE file for details

## 👤 Author

Kunal Poonia - [GitHub](https://github.com/KunalPoonia)

---

**Note:** This project is under active development. Check back for updates!
