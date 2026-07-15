"""
Ingestion module - converts a subject's source material into chunked text with
metadata. Multi-subject: each subject declares its own source + how to slice it.

Two ingestion "kinds" are supported:
    pdf_pages        - a PDF sliced by page ranges into named sections
                       (OSTEP: 5 chapters, tagged {chapter_name, page_number}).
    markdown_sections- a markdown file sliced by "## " headers into named
                       sections (DSA notes: 9 topics, tagged {chapter_name}).

Both feed the SAME downstream pipeline (embed_store -> retrieve -> evaluate),
which is the whole point of the DSA extension: prove the pipeline generalizes
to a second subject without special-casing it.

The chunks produced here are what embed_store.py embeds into ChromaDB.
Run this file directly to print a subject's chunks and eyeball them:

    python src/ingest.py            # defaults to OSTEP
    python src/ingest.py dsa        # DSA notes
"""

import sys
from pathlib import Path

from pypdf import PdfReader


# --- Configuration -----------------------------------------------------------

# Resolve paths relative to THIS file (not the CWD), so it works no matter which
# folder you run from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# The 5 confirmed OSTEP chapters and their page ranges.
# NOTE: 0-indexed pypdf page numbers (already adjusted from the printed page
# numbers). Format: (first_page, last_page), inclusive on both ends.
OSTEP_CHAPTERS = {
    "Introduction to OS": (23, 40),
    "Scheduling Intro": (82, 93),
    "Address Spaces": (131, 139),
    "Concurrency Intro": (283, 297),
    "Concurrency Problems (Deadlocks)": (378, 392),
}

# Per-subject corpus definitions. `collection` is the ChromaDB collection name
# embed_store.py will use (one collection per subject keeps them isolated and
# leaves the existing OSTEP data untouched).
SUBJECT_CORPORA = {
    "os": {
        "kind": "pdf_pages",
        "path": DATA_DIR / "ostep.pdf",
        "collection": "ostep",
        "sections": OSTEP_CHAPTERS,
    },
    "dsa": {
        "kind": "markdown_sections",
        "path": DATA_DIR / "dsa_notes.md",
        "collection": "dsa",
    },
}

# Chunking settings, in WORDS. 400 sits mid-range of the 300-500 target; we
# repeat the last 50 words of each chunk at the start of the next so a sentence
# split across a boundary isn't lost. Shared by both ingestion kinds.
CHUNK_SIZE = 400   # words per chunk
OVERLAP = 50       # words shared between neighbouring chunks


# --- Helpers exposed to the rest of the pipeline -----------------------------

def get_collection_name(subject_id):
    """ChromaDB collection name for a subject (embed_store / retrieve use this)."""
    return SUBJECT_CORPORA[subject_id]["collection"]


def list_subject_ids():
    """Subject ids that have a corpus defined here."""
    return list(SUBJECT_CORPORA.keys())


# --- pdf_pages ingestion (OSTEP) ---------------------------------------------

def load_chapter_words(reader, start_page, end_page):
    """Read one chapter and return a list of (word, page_number) tuples, so each
    chunk can later be tagged with the page it started on."""
    words_with_pages = []
    for page_number in range(start_page, end_page + 1):
        page_text = reader.pages[page_number].extract_text() or ""
        for word in page_text.split():
            words_with_pages.append((word, page_number))
    return words_with_pages


def chunk_chapter(words_with_pages, chapter_name):
    """Turn a chapter's (word, page) list into chunk dicts
    {text, chapter_name, page_number} (page = where the chunk starts)."""
    chunks = []
    total_words = len(words_with_pages)
    step = CHUNK_SIZE - OVERLAP
    start = 0

    while start < total_words:
        end = start + CHUNK_SIZE
        window = words_with_pages[start:end]
        words = [word for word, _page in window]
        chunks.append({
            "text": " ".join(words),
            "chapter_name": chapter_name,
            "page_number": window[0][1],
        })
        if end >= total_words:
            break
        start += step

    return chunks


def get_pdf_page_chunks(config):
    """Ingest a pdf_pages subject (OSTEP): one flat list of chunk dicts."""
    reader = PdfReader(str(config["path"]))
    all_chunks = []
    for chapter_name, (start_page, end_page) in config["sections"].items():
        words_with_pages = load_chapter_words(reader, start_page, end_page)
        all_chunks.extend(chunk_chapter(words_with_pages, chapter_name))
    return all_chunks


# --- markdown_sections ingestion (DSA) ---------------------------------------

def load_markdown_sections(path):
    """Split a markdown file into (section_title, body) pairs on "## " headers.

    Anything before the first "## " header (the "# " title, comments, intro
    prose) is ignored, so only the real topic sections become corpus content.
    """
    text = Path(path).read_text(encoding="utf-8")
    sections = []
    title = None
    body_lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            if title is not None:
                sections.append((title, "\n".join(body_lines).strip()))
            title = line[3:].strip()
            body_lines = []
        elif title is not None:
            body_lines.append(line)
    if title is not None:
        sections.append((title, "\n".join(body_lines).strip()))
    return sections


def chunk_section(text, section_name):
    """Chunk a section's plain text into {text, chapter_name} dicts (no page
    number - markdown sections aren't paginated). Reuses CHUNK_SIZE/OVERLAP."""
    words = text.split()
    chunks = []
    total_words = len(words)
    step = CHUNK_SIZE - OVERLAP
    start = 0

    if total_words == 0:
        return chunks

    while start < total_words:
        end = start + CHUNK_SIZE
        chunks.append({
            "text": " ".join(words[start:end]),
            "chapter_name": section_name,
        })
        if end >= total_words:
            break
        start += step

    return chunks


def get_markdown_chunks(config):
    """Ingest a markdown_sections subject (DSA): one flat list of chunk dicts,
    each tagged with its topic name (the "## " header)."""
    all_chunks = []
    for title, body in load_markdown_sections(config["path"]):
        all_chunks.extend(chunk_section(body, title))
    return all_chunks


# --- Public entry point -------------------------------------------------------

def get_chunks(subject_id="os"):
    """Return one flat list of chunk dicts for a subject. embed_store.py imports
    this. OSTEP behaviour is unchanged; new subjects dispatch on their `kind`."""
    if subject_id not in SUBJECT_CORPORA:
        raise ValueError(
            f"Unknown subject '{subject_id}'. Known: {list_subject_ids()}"
        )
    config = SUBJECT_CORPORA[subject_id]
    kind = config["kind"]
    if kind == "pdf_pages":
        return get_pdf_page_chunks(config)
    if kind == "markdown_sections":
        return get_markdown_chunks(config)
    raise ValueError(f"Unknown ingestion kind '{kind}' for subject '{subject_id}'.")


# --- Run directly to verify a subject's output --------------------------------

if __name__ == "__main__":
    # UTF-8 so previews with special characters print on the Windows console.
    sys.stdout.reconfigure(encoding="utf-8")

    subject_id = sys.argv[1] if len(sys.argv) > 1 else "os"
    chunks = get_chunks(subject_id)

    config = SUBJECT_CORPORA[subject_id]
    print(f"Subject: {subject_id}  ({config['kind']})")
    print(f"Source:  {config['path']}")
    print(f"Total chunks produced: {len(chunks)}\n")

    # Per-section count.
    sections = {}
    for c in chunks:
        sections[c["chapter_name"]] = sections.get(c["chapter_name"], 0) + 1
    print("Chunks per section:")
    for name, count in sections.items():
        print(f"  {name}: {count}")
    print()

    for i, chunk in enumerate(chunks):
        word_count = len(chunk["text"].split())
        preview = chunk["text"][:200].replace("\n", " ")
        page = f", page {chunk['page_number']}" if "page_number" in chunk else ""
        print(f"--- Chunk {i} [{chunk['chapter_name']}{page}, {word_count} words] ---")
        print(preview + ("..." if len(chunk["text"]) > 200 else ""))
        print()
