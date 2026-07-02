"""
Streamlit UI for MockMentor - the front door that ties the whole RAG loop
together for interactive testing.

Flow per turn:
    pick/receive a question
        -> student types an answer
        -> retrieve.py pulls the relevant OSTEP chunks
        -> evaluate.py grades the answer against those chunks (qwen3:8b)
        -> we show verdict / score / explanation / sources
        -> the model's follow-up becomes the next question (adaptive loop)

This is our testing UI (Streamlit only for now); the liquid-glass mockups are
a later polish pass. Run it from the project root with:

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

# A few starter questions per chapter to kick off a session. Once a session is
# going, the model's follow-up questions drive it adaptively from here.
QUESTION_BANK = {
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
}


# --- Cached resources ---------------------------------------------------------

@st.cache_resource
def load_collection():
    """Open the ChromaDB collection once and reuse it across reruns.

    Streamlit re-executes this whole script on every interaction, so without
    caching we'd reopen the store (and reload the embedding model) every click.
    @st.cache_resource keeps one shared instance alive for the session.
    """
    return get_collection()


# --- Session state ------------------------------------------------------------

def init_state():
    """Set up the per-session state we carry across reruns."""
    if "question" not in st.session_state:
        st.session_state.question = None      # the question currently being asked
    if "result" not in st.session_state:
        st.session_state.result = None        # the last grading result to display
    if "turn" not in st.session_state:
        st.session_state.turn = 0             # counts graded answers this session


def set_question(question):
    """Make `question` the active question and clear the previous result."""
    st.session_state.question = question
    st.session_state.result = None


# --- UI -----------------------------------------------------------------------

st.set_page_config(page_title="MockMentor", page_icon="🎓")
init_state()

st.title("🎓 MockMentor")
st.caption("Local RAG mock interviewer, grounded in the OSTEP textbook.")

collection = load_collection()

# Sidebar: pick a chapter + starter question to begin (or restart) a session.
with st.sidebar:
    st.header("Start a question")
    chapter = st.selectbox("Chapter", list(QUESTION_BANK.keys()))
    starter = st.selectbox("Question", QUESTION_BANK[chapter])
    if st.button("Ask this question", use_container_width=True):
        set_question(starter)
        st.session_state.turn = 0
    st.divider()
    st.caption(f"Model: qwen3:8b • Corpus: {collection.count()} chunks")

# Main pane: only show the answer flow once a question is active.
if st.session_state.question is None:
    st.info("Pick a chapter and question in the sidebar to begin.")
else:
    st.subheader("Interview question")
    st.write(st.session_state.question)

    answer = st.text_area(
        "Your answer",
        height=160,
        placeholder="Answer as you would out loud in an interview...",
        key=f"answer_{st.session_state.turn}",   # fresh box each turn
    )

    if st.button("Submit answer", type="primary"):
        if not answer.strip():
            st.warning("Type an answer before submitting.")
        else:
            with st.spinner("Retrieving context and grading (first call loads the model)..."):
                # One retrieval, reused for grading, so the UI can also show
                # the exact chunks the grade was based on.
                chunks = retrieve(st.session_state.question, collection=collection)
                result = grade_answer(
                    st.session_state.question, answer, chunks=chunks
                )
            st.session_state.result = result

# Show the most recent grading result, if any.
result = st.session_state.result
if result is not None:
    st.divider()

    verdict = result.get("verdict") or "Unknown"
    score = result.get("score")
    # Color the verdict roughly by how well it went.
    if verdict == "Correct":
        st.success(f"**{verdict}** — {score}/5")
    elif verdict == "Partially Correct":
        st.warning(f"**{verdict}** — {score}/5")
    else:
        st.error(f"**{verdict}** — {score}/5")

    st.markdown("**Feedback**")
    st.write(result.get("explanation") or "_No explanation returned._")

    follow_up = result.get("follow_up_question")
    if follow_up:
        st.markdown("**Follow-up question**")
        st.write(follow_up)
        if st.button("Answer the follow-up →"):
            set_question(follow_up)
            st.session_state.turn += 1
            st.rerun()

    # Show what the grade was grounded in - the RAG receipts.
    sources = result.get("sources") or []
    if sources:
        with st.expander("Sources used for grading"):
            for s in sources:
                st.write(f"- {s['chapter_name']} (page {s['page_number']})")
