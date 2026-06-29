"""
PDF ingestion module - converts the OSTEP PDF into chunked text with metadata.

Pipeline:
    ostep.pdf  ->  extract text from 5 chapter page-ranges
               ->  split each chapter into overlapping word-chunks
               ->  tag every chunk with {chapter_name, page_number}

The chunks produced here are what embed_store.py will later embed into ChromaDB.
Run this file directly to print the chunks and eyeball that everything looks right:

    python src/ingest.py
"""

import sys
from pathlib import Path

from pypdf import PdfReader


# --- Configuration -----------------------------------------------------------

# Resolve the PDF path relative to THIS file (not the current working directory),
# so `python src/ingest.py` works no matter which folder you run it from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = PROJECT_ROOT / "data" / "raw" / "ostep.pdf"

# The 5 confirmed OSTEP chapters and their page ranges.
# NOTE: these are 0-indexed pypdf page numbers (already adjusted from the
# printed page numbers in the roadmap table). Format: (first_page, last_page),
# inclusive on both ends.
CHAPTERS = {
    "Introduction to OS": (23, 40),
    "Scheduling Intro": (82, 93),
    "Address Spaces": (131, 139),
    "Concurrency Intro": (283, 297),
    "Concurrency Problems (Deadlocks)": (378, 392),
}

# Chunking settings. We measure chunk size in WORDS (simple and good enough
# for a first pass). 400 sits in the middle of the roadmap's 300-500 range,
# and we repeat the last 50 words of each chunk at the start of the next one
# so a sentence split across a boundary isn't lost.
CHUNK_SIZE = 400   # words per chunk
OVERLAP = 50       # words shared between neighbouring chunks


# --- Step 1: read a chapter's words, remembering which page each came from ----

def load_chapter_words(reader, start_page, end_page):
    """Read one chapter and return a list of (word, page_number) tuples.

    We keep the page number alongside each word so that later, when we group
    words into chunks, we can tag each chunk with the page it started on.
    """
    words_with_pages = []
    for page_number in range(start_page, end_page + 1):
        # extract_text() can return None for an empty/image-only page, so
        # fall back to "" to keep .split() from crashing.
        page_text = reader.pages[page_number].extract_text() or ""
        for word in page_text.split():
            words_with_pages.append((word, page_number))
    return words_with_pages


# --- Step 2: split one chapter's words into overlapping chunks ----------------

def chunk_chapter(words_with_pages, chapter_name):
    """Turn a chapter's (word, page) list into a list of chunk dictionaries.

    Each chunk is a dict: {"text", "chapter_name", "page_number"}.
    'page_number' is the page where the chunk *starts* - good enough for
    citing a source later.
    """
    chunks = []
    total_words = len(words_with_pages)

    # We slide a window of CHUNK_SIZE words across the chapter, advancing by
    # (CHUNK_SIZE - OVERLAP) each time so consecutive windows overlap.
    step = CHUNK_SIZE - OVERLAP
    start = 0

    while start < total_words:
        end = start + CHUNK_SIZE
        window = words_with_pages[start:end]  # list of (word, page) tuples

        # Separate the words from the page numbers for this window.
        words = [word for word, _page in window]
        chunk_text = " ".join(words)
        start_page = window[0][1]  # page number of the first word in the chunk

        chunks.append({
            "text": chunk_text,
            "chapter_name": chapter_name,
            "page_number": start_page,
        })

        # If this window reached the end of the chapter, we're done - break so
        # we don't emit a tiny trailing chunk made only of overlap.
        if end >= total_words:
            break
        start += step

    return chunks


# --- Step 3: tie it together: PDF -> all chunks -------------------------------

def get_chunks():
    """Read the OSTEP PDF and return one flat list of chunk dicts for all 5
    chapters. This is the function embed_store.py will import later."""
    reader = PdfReader(str(PDF_PATH))

    all_chunks = []
    for chapter_name, (start_page, end_page) in CHAPTERS.items():
        words_with_pages = load_chapter_words(reader, start_page, end_page)
        chapter_chunks = chunk_chapter(words_with_pages, chapter_name)
        all_chunks.extend(chapter_chunks)

    return all_chunks


# --- Step 4: run directly to verify the output --------------------------------

if __name__ == "__main__":
    # The OSTEP PDF contains special characters (e.g. the "fi" ligature),
    # and the default Windows console (cp1252) can't print them. Switch this
    # script's output to UTF-8 so the previews print without crashing.
    sys.stdout.reconfigure(encoding="utf-8")

    chunks = get_chunks()

    print(f"PDF: {PDF_PATH}")
    print(f"Total chunks produced: {len(chunks)}\n")

    # Show a per-chapter count so you can confirm every chapter was picked up.
    print("Chunks per chapter:")
    for chapter_name in CHAPTERS:
        count = sum(1 for c in chunks if c["chapter_name"] == chapter_name)
        print(f"  {chapter_name}: {count}")
    print()

    # Print every chunk with a short text preview so you can spot-check that
    # the text and metadata look sensible.
    for i, chunk in enumerate(chunks):
        word_count = len(chunk["text"].split())
        preview = chunk["text"][:200].replace("\n", " ")
        print(f"--- Chunk {i} "
              f"[{chunk['chapter_name']}, page {chunk['page_number']}, "
              f"{word_count} words] ---")
        print(preview + ("..." if len(chunk["text"]) > 200 else ""))
        print()
