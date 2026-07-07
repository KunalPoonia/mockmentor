"""
Web server for MockMentor - serves the liquid-glass single-page UI and exposes
the RAG pipeline over a small JSON API.

This is the bridge the static HTML couldn't cross on its own: the browser can't
call retrieve.py / evaluate.py directly (that's a Python process), so this Flask
app sits in the middle -

    browser (index.html + JS)
        GET  /                 -> the single-page app
        GET  /api/subjects     -> subject catalogue for the selector
        GET  /api/question     -> next seed question for a subject
        POST /api/grade        -> {question, answer} -> graded result JSON

We open the ChromaDB collection ONCE at startup (loading it - and the embedding
model - on every request would be painfully slow) and reuse it across calls.

Run from the project root (inside the venv):

    python src/server.py

then open http://localhost:5000 . Requires Ollama running with qwen3:8b and a
built chroma_db/ (run `python src/embed_store.py` once first).
"""

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

# Flat imports, matching the rest of src/. Running `python src/server.py` puts
# src/ on the path so these resolve.
from embed_store import get_collection
from evaluate import grade_answer
from questions import get_questions, get_subjects
from retrieve import retrieve


# --- Paths -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# The single-page UI lives in the UI folder as index.html (built to
# be self-contained: Tailwind via CDN, inline styles + JS).
UI_DIR = PROJECT_ROOT / "UI"

app = Flask(__name__)
# Dev: never let the browser cache the UI files, so edits to index.html / CSS
# show up on a normal refresh instead of serving a stale cached copy.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Open the vector store once at import time and hand the same handle to every
# request. get_collection() also loads the embedding model, so we very much
# want this to happen a single time, not per request.
collection = get_collection()


# --- Page --------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page app."""
    return send_from_directory(UI_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static files (videos, images, etc.) from the UI directory."""
    return send_from_directory(UI_DIR, filename)


# --- API ---------------------------------------------------------------------

@app.route("/api/subjects")
def api_subjects():
    """Return the subject catalogue so the selector can render its cards."""
    return jsonify(get_subjects())


@app.route("/api/question")
def api_question():
    """Return one seed question for a subject.

    Query params:
        subject: subject id (default "os")
        index:   which seed question to serve (default 0), so the UI can walk
                 through the bank as "Question N of 10".
    """
    subject = request.args.get("subject", "os")
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0

    questions = get_questions(subject)
    if not questions:
        return jsonify({"error": f"No questions available for '{subject}'."}), 404

    # Wrap around if the index runs past the end of the bank.
    index = index % len(questions)
    return jsonify(
        {
            "subject": subject,
            "index": index,
            "total": len(questions),
            "question": questions[index],
        }
    )


@app.route("/api/grade", methods=["POST"])
def api_grade():
    """Grade a student's answer against the retrieved OSTEP context.

    Expects JSON: {"question": "...", "answer": "..."}
    Returns the grade_answer() result (verdict, score, explanation,
    model_answer, follow_up_question, sources).
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()

    if not question:
        return jsonify({"error": "Missing question."}), 400
    if not answer:
        return jsonify({"error": "Please enter an answer before submitting."}), 400

    # Retrieve once, reuse for grading - and hand the chunks to grade_answer so
    # the returned "sources" match exactly what was used.
    try:
        chunks = retrieve(question, collection=collection)
        result = grade_answer(question, answer, chunks=chunks)
    except ConnectionError:
        # Most common failure: Ollama isn't running. Return a clean JSON message
        # the frontend can display instead of a raw 500 HTML page.
        return jsonify({
            "error": "Couldn't reach the local model. Make sure Ollama is "
                     "running (try `ollama list`) with qwen3:8b pulled."
        }), 503
    except Exception as exc:
        # Anything else (bad JSON from the model, etc.) - surface it cleanly.
        return jsonify({"error": f"Grading failed: {exc}"}), 500

    return jsonify(result)


if __name__ == "__main__":
    # debug=False: the RAG pipeline + model load make the reloader restart
    # slow and it would re-open ChromaDB twice. Threaded so the UI stays
    # responsive while a grade is in flight.
    print("MockMentor server -> http://localhost:5000  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
