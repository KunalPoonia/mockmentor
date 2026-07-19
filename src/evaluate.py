"""
Evaluation module - the "G" in RAG (grounded generation), used here for grading.

Given an interview question, the student's answer, and the OSTEP chunks we
retrieved for that question, ask the local LLM to grade the answer *against the
textbook passages* - not against its own general knowledge. This is the whole
point of RAG for a study tool: the grade and feedback are anchored to the
actual course material the student is expected to learn.

Pipeline:
    question + student_answer + retrieved chunks
        ->  build a grading prompt that includes the chunks as "context"
        ->  qwen3:8b returns structured JSON
        ->  parse into {verdict, score, explanation, follow_up_question}

Why qwen3:8b: its reasoning helps judge partially-correct answers. Its one
quirk is a "thinking mode" that emits <think>...</think> before the real
answer, so we (a) send "/no_think" to switch it off and (b) still strip any
stray tags and extract the JSON defensively. llama3.1:8b is the fallback if
qwen3's output ever proves too fussy - pass model="llama3.1:8b".

Run this file directly for a demo grade over one hard-coded Q/A:

    python src/evaluate.py
"""

import json
import re

import ollama

# retrieve lives alongside this file in src/; flat import matches the rest of
# the project (embed_store's `from ingest import ...`, retrieve's `from
# embed_store import ...`). Resolves under `python src/evaluate.py` and when
# imported by the Flask server.
from retrieve import retrieve
from questions import get_subjects


# --- Configuration -----------------------------------------------------------

# Primary grading model. llama3.1:8b is the tested fallback (no <think> quirk).
MODEL = "qwen3:8b"

# Low temperature: grading should be about as deterministic as we can make it,
# so the same answer doesn't swing between "Correct" and "Incorrect" on reruns.
TEMPERATURE = 0.2

# The shape we ask the model to return. Keeping this in one place makes the
# prompt and the parser agree on the exact keys.
EXPECTED_KEYS = (
    "verdict",
    "score",
    "explanation",
    "model_answer",
    "follow_up_question",
)


# --- Prompt construction ------------------------------------------------------

def format_context(chunks):
    """Turn retrieved chunks into a readable, cited context block for the prompt.

    Each chunk is labelled with its chapter + page so the model can (and is
    told to) ground its feedback in specific passages.
    """
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        # Page number only exists for paginated corpora (OSTEP); DSA topics are
        # cited by section name alone.
        if "page_number" in chunk:
            source = f"{chunk['chapter_name']}, page {chunk['page_number']}"
        else:
            source = chunk["chapter_name"]
        blocks.append(f"[Source {i} - {source}]\n{chunk['text']}")
    return "\n\n".join(blocks)


def build_messages(question, student_answer, chunks, subject_name="Operating Systems"):
    """Build the chat messages for the grading call.

    We split responsibilities: a system message fixes the role + output
    contract, and the user message carries the actual question, context, and
    answer. "/no_think" (system) disables qwen3's thinking mode. `subject_name`
    sets the interviewer's domain so the same grader works for any subject.
    """
    context = format_context(chunks)

    system = (
        "/no_think\n"
        f"You are a strict but fair {subject_name} interviewer grading a "
        "student's spoken answer. Grade ONLY against the provided reference "
        "context, not your own outside knowledge. If the context does not "
        "support a claim, do not credit it.\n\n"
        "Return ONLY a single JSON object, no prose, with exactly these keys:\n"
        '  "verdict": one of "Correct", "Partially Correct", "Incorrect"\n'
        '  "score": integer 0-5 (0 = no relevant content, 5 = complete & accurate)\n'
        '  "explanation": 1-3 sentences on what was right/wrong, citing the '
        "context (e.g. mention the relevant section/source).\n"
        '  "model_answer": a concise, correct answer to the question (2-4 '
        "sentences), drawn ONLY from the context, showing the student what a "
        "strong answer looks like.\n"
        '  "follow_up_question": one adaptive next question. If the answer was '
        "weak, probe the same concept more simply; if strong, go deeper or to a "
        "related idea. Must be answerable from the same context."
    )

    user = (
        f"Textbook context:\n{context}\n\n"
        f"Interview question:\n{question}\n\n"
        f"Student's answer:\n{student_answer}\n\n"
        "Grade the answer now and respond with the JSON object only."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# --- Robust JSON parsing ------------------------------------------------------

def parse_response(raw):
    """Pull a clean result dict out of the model's raw text.

    Defensive on purpose: even with /no_think + format=json we strip any stray
    <think> block and grab the outermost {...} before json.loads, so one odd
    generation doesn't crash the app.
    """
    # Drop any leftover thinking block (qwen3 quirk) before looking for JSON.
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Grab the outermost JSON object if the model wrapped it in any extra text.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output:\n{raw}")

    data = json.loads(match.group(0))

    # Normalise: guarantee every expected key exists so callers (the web UI)
    # can render without KeyErrors even if the model omitted one.
    for key in EXPECTED_KEYS:
        data.setdefault(key, None)

    # Coerce score to an int when possible; leave as-is if the model got creative.
    if data["score"] is not None:
        try:
            data["score"] = int(data["score"])
        except (TypeError, ValueError):
            pass

    return data


# --- Public API ---------------------------------------------------------------

def grade_answer(question, student_answer, chunks=None, k=3, model=MODEL, subject="os"):
    """Grade a student's answer against retrieved context for a subject.

    Args:
        question:       The interview question that was asked.
        student_answer: The student's response text.
        chunks:         Pre-retrieved chunks (from retrieve.retrieve()). If
                        None, we retrieve them here. Pass them in from the app
                        so retrieval and grading share one lookup.
        k:              How many chunks to retrieve when chunks is None.
        model:          Ollama model name (default qwen3:8b).
        subject:        Subject id (e.g. "os", "dsa"). Sets the interviewer's
                        domain and, when chunks aren't passed, which collection
                        to retrieve from.

    Returns:
        dict with keys: verdict, score, explanation, model_answer,
        follow_up_question, plus "sources" (the chunks used) so the UI can show
        what grounded it.
    """
    if chunks is None:
        chunks = retrieve(question, k=k, subject=subject)

    # Human-readable subject name for the interviewer role (falls back to the id).
    subject_name = get_subjects().get(subject, {}).get("name", "Operating Systems")
    messages = build_messages(question, student_answer, chunks, subject_name=subject_name)

    response = ollama.chat(
        model=model,
        messages=messages,
        format="json",              # ask Ollama to constrain output to JSON
        options={"temperature": TEMPERATURE},
    )
    raw = response["message"]["content"]

    result = parse_response(raw)
    # Attach the sources we graded against so the UI can cite them. Page number
    # is included only for paginated corpora (OSTEP); DSA topics cite by name.
    sources = []
    for c in chunks:
        src = {"chapter_name": c["chapter_name"]}
        if "page_number" in c:
            src["page_number"] = c["page_number"]
        sources.append(src)
    result["sources"] = sources
    return result


# --- Run directly for a demo grade --------------------------------------------

if __name__ == "__main__":
    question = "What is a deadlock, and what conditions cause it?"
    # A partially-correct answer on purpose, to see nuanced grading.
    student_answer = (
        "A deadlock is when two threads get stuck waiting for each other and "
        "neither can continue. It happens because of locks."
    )

    print(f"Question:       {question}")
    print(f"Student answer: {student_answer}\n")
    print(f"Grading with {MODEL} (this loads the model on first call)...\n")

    result = grade_answer(question, student_answer)

    print(f"Verdict:      {result['verdict']}")
    print(f"Score:        {result['score']}/5")
    print(f"Explanation:  {result['explanation']}")
    print(f"Model answer: {result['model_answer']}")
    print(f"Follow-up:    {result['follow_up_question']}")
    print("Graded against:")
    for s in result["sources"]:
        page = f" (page {s['page_number']})" if "page_number" in s else ""
        print(f"  - {s['chapter_name']}{page}")
