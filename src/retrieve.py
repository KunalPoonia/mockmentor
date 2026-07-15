"""
Retrieval module - the "R" in RAG.

Given a question and a subject, find the most relevant chunks from that
subject's ChromaDB collection. This is the bridge between the raw question and
the LLM: instead of grading from memory, we pull the actual source passages the
answer should be based on, then hand those to evaluate.py.

Pipeline:
    question (str)  ->  embed with the SAME model used in embed_store.py
                    ->  ChromaDB (subject's collection) finds the k nearest
                    ->  return those chunks (text + section + [page] + distance)

We reuse embed_store.get_collection(subject) rather than opening ChromaDB
ourselves, so the query model matches the storage model exactly (otherwise the
vectors stop being comparable and retrieval silently goes junk).

Run this file directly to sanity-check retrieval per subject:

    python src/retrieve.py            # OSTEP
    python src/retrieve.py dsa        # DSA
"""

import sys

from embed_store import get_collection


# --- Configuration -----------------------------------------------------------

# How many chunks to pull per question. k=3 gives enough grading context
# without drowning the LLM in text.
DEFAULT_K = 3


# --- Core retrieval -----------------------------------------------------------

def retrieve(question, k=DEFAULT_K, collection=None, subject="os"):
    """Return the k chunks most relevant to `question` for a subject.

    Args:
        question:   The query text.
        k:          How many chunks to return (default 3).
        collection: Optional pre-opened ChromaDB collection (a long-running app
                    opens each subject's store once and passes it in). If None,
                    we open the collection for `subject`.
        subject:    Subject id, used to pick the collection when one isn't
                    passed in. Defaults to "os".

    Returns:
        A list of dicts, best match first:
            {"text", "chapter_name", "distance"[, "page_number"]}
        `page_number` is only present for paginated corpora (OSTEP), not for
        section-based ones (DSA topics).
    """
    if collection is None:
        collection = get_collection(subject)

    results = collection.query(query_texts=[question], n_results=k)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        chunk = {
            "text": text,
            "chapter_name": metadata.get("chapter_name", "Unknown"),
            "distance": distance,
        }
        # Carry page number through only when the corpus has one.
        if "page_number" in metadata:
            chunk["page_number"] = metadata["page_number"]
        chunks.append(chunk)
    return chunks


# --- Run directly to sanity-check retrieval -----------------------------------

if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "os"

    # Each question is paired with the section we EXPECT it to retrieve from,
    # proving semantic search pulls the right source for a known question.
    test_suites = {
        "os": [
            ("How does the OS decide which process to run next?", "Scheduling Intro"),
            ("What is a virtual address space?", "Address Spaces"),
            ("Why can two threads deadlock?", "Concurrency Problems (Deadlocks)"),
        ],
        "dsa": [
            ("When would you use a sliding window?", "Sliding Window"),
            ("How do you detect a cycle in a linked list?", "Linked Lists"),
            ("What makes dynamic programming efficient?", "Dynamic Programming (intro-level)"),
        ],
    }
    test_cases = test_suites.get(subject, [])

    collection = get_collection(subject)
    print(f"[{subject}] Collection holds {collection.count()} chunks.\n")

    passed = 0
    for question, expected_section in test_cases:
        chunks = retrieve(question, collection=collection, subject=subject)
        top_section = chunks[0]["chapter_name"] if chunks else "(none)"
        ok = top_section == expected_section
        passed += ok

        print(f"Q: {question}")
        print(f"   expected: {expected_section}")
        print(f"   top hit : {top_section}  {'PASS' if ok else 'FAIL'}")
        for chunk in chunks:
            page = f", page {chunk['page_number']}" if "page_number" in chunk else ""
            print(f"     - {chunk['chapter_name']}{page} (distance {chunk['distance']:.3f})")
        print()

    print(f"Sanity check: {passed}/{len(test_cases)} questions hit the right section.")
