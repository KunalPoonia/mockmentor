"""
Streamlit UI for MockMentor - the front door that ties the whole RAG loop
together for interactive testing (and demoing).

Flow per turn:
    pick/receive a question
        -> student types an answer
        -> retrieve.py pulls the relevant OSTEP chunks
        -> evaluate.py grades the answer against those chunks (qwen3:8b)
        -> we show verdict / score / explanation / model answer / sources
        -> the model's follow-up becomes the next question (adaptive loop)

This is one of two front ends over the same pipeline (the other is the
liquid-glass web app in server.py / UI/index.html). Switch between them with
the launcher at the project root:

    python run.py streamlit   # this one
    python run.py web         # the liquid-glass one

Or run it directly from the project root with:

    streamlit run src/app.py

(Requires Ollama running with qwen3:8b, and a built chroma_db/ from Step 2.2.)
"""

import streamlit as st

# Flat imports: `streamlit run src/app.py` puts src/ on the path, matching the
# rest of the project's import style.
from embed_store import get_collection
from evaluate import grade_answer
from retrieve import retrieve


# --- Seed question bank -------------------------------------------------------

# Nested by subject -> chapter -> starter questions. Only "Operating Systems"
# has a built corpus right now (the OSTEP chapters in ChromaDB), so it's the
# only subject offered in the dropdown below. Add a new top-level key here
# once another subject's corpus exists, and the Chapter/Question dropdowns
# will pick it up automatically.
SUBJECT_QUESTION_BANKS = {
    "Operating Systems": {
        "Introduction to OS": [
            "What is an operating system and what problem does virtualization solve?",
            "What does it mean for the OS to be a 'resource manager'?",
        ],
        "Scheduling Intro": [
            "What is the Shortest Job First scheduling policy and what problem does it have?",
            "How does round robin scheduling improve response time?",
        ],
        "Address Spaces": [
            "What is a virtual address space and why does the OS give each process one?",
            "What are the three goals of virtual memory?",
        ],
        "Concurrency Intro": [
            "What is a race condition and why does it happen?",
            "What is a critical section and how do we protect it?",
        ],
        "Concurrency Problems (Deadlocks)": [
            "What is a deadlock, and what conditions cause it?",
            "How can circular wait be prevented?",
        ],
    },
}


# --- Page setup ----------------------------------------------------------------

st.set_page_config(
    page_title="MockMentor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A light stylesheet layered on top of Streamlit's defaults - just enough to
# make verdicts, cards, and the header feel intentional instead of default.
st.markdown(
    """
    <style>
      .mm-hero {
          padding: 1.1rem 1.4rem; border-radius: 14px; margin-bottom: 1.2rem;
          background: linear-gradient(135deg, rgba(99,102,241,0.16), rgba(99,102,241,0.03));
          border: 1px solid rgba(99,102,241,0.25);
      }
      .mm-hero h1 { margin: 0 0 0.15rem 0; font-size: 1.6rem; }
      .mm-hero p { margin: 0; opacity: 0.75; font-size: 0.92rem; }

      .mm-qcard {
          padding: 1.3rem 1.5rem; border-radius: 14px; margin-bottom: 1rem;
          background: rgba(148,163,184,0.08); border: 1px solid rgba(148,163,184,0.18);
      }
      .mm-qcard .mm-qlabel {
          font-size: 0.75rem; letter-spacing: 0.06em; text-transform: uppercase;
          opacity: 0.6; margin-bottom: 0.35rem;
      }
      .mm-qcard .mm-qtext { font-size: 1.15rem; font-weight: 600; line-height: 1.45; }

      .mm-verdict {
          display: inline-flex; align-items: center; gap: 0.4rem;
          padding: 0.3rem 0.9rem; border-radius: 999px; font-weight: 600;
          font-size: 0.85rem; letter-spacing: 0.02em;
      }
      .mm-verdict-correct   { background: rgba(76,175,80,0.16);  color: #4caf50; border: 1px solid rgba(76,175,80,0.35); }
      .mm-verdict-partial   { background: rgba(255,179,0,0.16);  color: #ffb300; border: 1px solid rgba(255,179,0,0.35); }
      .mm-verdict-incorrect { background: rgba(244,67,54,0.16);  color: #f44336; border: 1px solid rgba(244,67,54,0.35); }

      .mm-model-answer {
          padding: 1rem 1.2rem; border-radius: 12px; margin-top: 0.4rem;
          background: rgba(99,179,237,0.08); border: 1px solid rgba(99,179,237,0.22);
      }
      .mm-followup {
          padding: 1rem 1.2rem; border-radius: 12px; margin-top: 0.4rem;
          background: rgba(186,104,255,0.08); border: 1px solid rgba(186,104,255,0.22);
      }
      .mm-hist-row {
          padding: 0.7rem 1rem; border-radius: 10px; margin-bottom: 0.5rem;
          background: rgba(148,163,184,0.06); border: 1px solid rgba(148,163,184,0.14);
      }
      div[data-testid="stMetric"] {
          background: rgba(148,163,184,0.07); border: 1px solid rgba(148,163,184,0.16);
          border-radius: 12px; padding: 0.6rem 0.9rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Cached resources ------------------------------------------------------------

@st.cache_resource
def load_collection():
    """Open the ChromaDB collection once and reuse it across reruns.

    Streamlit re-executes this whole script on every interaction, so without
    caching we'd reopen the store (and reload the embedding model) every click.
    @st.cache_resource keeps one shared instance alive for the session.
    """
    return get_collection()


VERDICT_META = {
    "Correct":           {"cls": "mm-verdict-correct",   "icon": "✅"},
    "Partially Correct": {"cls": "mm-verdict-partial",   "icon": "⚠️"},
    "Incorrect":         {"cls": "mm-verdict-incorrect", "icon": "❌"},
}


# --- Session state ---------------------------------------------------------------

def init_state():
    """Set up the per-session state we carry across reruns."""
    defaults = {
        "question": None,       # the question currently being asked
        "result": None,         # the last grading result to display
        "turn": 0,               # counts questions asked this session (fresh answer box each turn)
        "is_followup": False,    # whether the active question came from a follow-up
        "history": [],           # this session's graded answers, most recent last
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_question(question, is_followup=False):
    """Make `question` the active question and clear the previous result."""
    st.session_state.question = question
    st.session_state.result = None
    st.session_state.is_followup = is_followup
    st.session_state.turn += 1


init_state()
collection = load_collection()


# --- Sidebar: session control -----------------------------------------------------

with st.sidebar:
    st.markdown("### 🎓 MockMentor")
    st.caption("Local RAG mock interviewer")
    st.divider()

    st.markdown("**Start a question**")
    subject = st.selectbox("Subject", list(SUBJECT_QUESTION_BANKS.keys()))
    chapter_bank = SUBJECT_QUESTION_BANKS[subject]
    chapter = st.selectbox("Chapter", list(chapter_bank.keys()))
    starter = st.selectbox("Question", chapter_bank[chapter])
    if st.button("Answer this question", use_container_width=True, type="primary"):
        set_question(starter, is_followup=False)

    st.divider()

    # Live session stats.
    hist = st.session_state.history
    answered = len(hist)
    avg_score = (sum((h["score"] or 0) for h in hist) / answered) if answered else 0
    c1, c2 = st.columns(2)
    c1.metric("Answered", answered)
    c2.metric("Avg score", f"{avg_score:.1f}/5" if answered else "—")

    if hist and st.button("Clear session history", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption(f"Model: qwen3:8b (local, via Ollama)")
    st.caption(f"Corpus: {collection.count()} chunks · Operating Systems (OSTEP)")


# --- Header -----------------------------------------------------------------------

st.markdown(
    """
    <div class="mm-hero">
      <h1>MockMentor</h1>
      <p>A local, fully offline mock interviewer — grades your answers against the actual OSTEP textbook, not general knowledge, and adapts its follow-ups to what you got right or missed.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- Main pane: question + answer flow --------------------------------------------

if st.session_state.question is None:
    st.info("👈 Pick a chapter and starter question in the sidebar to begin.")
else:
    tag = "Follow-up question" if st.session_state.is_followup else "Interview question"
    st.markdown(
        f"""
        <div class="mm-qcard">
          <div class="mm-qlabel">{tag} · {subject}</div>
          <div class="mm-qtext">{st.session_state.question}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.text_area(
        "Your answer",
        height=160,
        placeholder="Answer as you would out loud in an interview...",
        key=f"answer_{st.session_state.turn}",   # fresh box each turn
        label_visibility="collapsed",
    )

    submit_col, _ = st.columns([1, 3])
    with submit_col:
        submit = st.button("Submit answer", type="primary", use_container_width=True)

    if submit:
        if not answer.strip():
            st.warning("Type an answer before submitting.")
        else:
            with st.spinner("Retrieving context and grading (first call loads the model)..."):
                # One retrieval, reused for grading, so the UI can also show
                # the exact chunks the grade was based on.
                chunks = retrieve(st.session_state.question, collection=collection)
                result = grade_answer(st.session_state.question, answer, chunks=chunks)
            st.session_state.result = result
            st.session_state.history.append({
                "question": st.session_state.question,
                "verdict": result.get("verdict"),
                "score": result.get("score"),
                "is_followup": st.session_state.is_followup,
            })
            # The sidebar (Answered / Avg score) renders BEFORE this block runs
            # each pass, so without a rerun the count looks stale until the next
            # interaction. Rerun now so it reflects the just-graded answer right away.
            st.rerun()

# --- Result: verdict, feedback, model answer, follow-up, sources -----------------

result = st.session_state.result
if result is not None:
    st.divider()

    verdict = result.get("verdict") or "Unknown"
    score = result.get("score")
    meta = VERDICT_META.get(verdict, {"cls": "mm-verdict-incorrect", "icon": "❔"})

    v_col, s_col = st.columns([3, 1])
    with v_col:
        st.markdown(
            f'<span class="mm-verdict {meta["cls"]}">{meta["icon"]} {verdict}</span>',
            unsafe_allow_html=True,
        )
    with s_col:
        st.metric("Score", f"{score if score is not None else '—'} / 5")

    st.markdown("**Feedback**")
    st.write(result.get("explanation") or "_No explanation returned._")

    model_answer = result.get("model_answer")
    if model_answer:
        st.markdown(
            f'<div class="mm-model-answer">💡 <b>Model answer</b><br>{model_answer}</div>',
            unsafe_allow_html=True,
        )

    follow_up = result.get("follow_up_question")
    if follow_up:
        st.markdown(
            f'<div class="mm-followup">🔁 <b>Follow-up</b><br>{follow_up}</div>',
            unsafe_allow_html=True,
        )
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            if st.button("Answer the follow-up →", use_container_width=True, type="primary"):
                set_question(follow_up, is_followup=True)
                st.rerun()
        with fcol2:
            if st.button("Re-answer this question", use_container_width=True):
                set_question(st.session_state.question, is_followup=st.session_state.is_followup)
                st.rerun()

    # Show what the grade was grounded in - the RAG receipts.
    sources = result.get("sources") or []
    if sources:
        with st.expander(f"📚 Sources used for grading ({len(sources)})"):
            for s in sources:
                st.write(f"- {s['chapter_name']} (page {s['page_number']})")


# --- Session history --------------------------------------------------------------

if st.session_state.history:
    st.divider()
    with st.expander(f"🕘 Session history ({len(st.session_state.history)} answered)", expanded=False):
        for i, h in enumerate(reversed(st.session_state.history), start=1):
            n = len(st.session_state.history) - i + 1
            meta = VERDICT_META.get(h["verdict"], {"cls": "mm-verdict-incorrect", "icon": "❔"})
            tag = "Follow-up" if h["is_followup"] else f"Q{n}"
            st.markdown(
                f"""
                <div class="mm-hist-row">
                  <div style="display:flex; justify-content:space-between; gap:0.75rem; align-items:center;">
                    <span style="opacity:0.65; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.04em;">{tag}</span>
                    <span class="mm-verdict {meta['cls']}">{meta['icon']} {h['verdict']} · {h['score'] if h['score'] is not None else '—'}/5</span>
                  </div>
                  <div style="margin-top:0.35rem;">{h['question']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
