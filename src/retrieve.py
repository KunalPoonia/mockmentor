"""
Retrieval module - the "R" in RAG.

Given a question, find the most relevant OSTEP chunks we stored back in
Step 2.2. This is the bridge between the raw question and the LLM: instead of
asking the model to grade from memory, we first pull the actual textbook
passages the answer should be based on, then hand those to evaluate.py later.

Pipeline:
    question (str)  ->  embed with the SAME model used in embed_store.py
                    ->  ChromaDB finds the k nearest chunk vectors
                    ->  return those chunks (text + chapter + page + score)

We deliberately reuse embed_store.get_collection() rather than opening ChromaDB
ourselves. That guarantees we query the exact same collection with the exact
same embedding function - if the query model and the storage model ever drift
apart, the vectors stop being comparable and retrieval silently goes junk.

Run this file directly to sanity-check retrieval against a few known questions:

    python src/retrieve.py
"""

# embed_store lives alongside this file in src/, so running from src/ (or
# importing src.retrieve) both resolve. We mirror ingest's flat-import style.
from embed_store import get_collection


# --- Configuration -----------------------------------------------------------

# How many chunks to pull back per question. k=3 is a good default for grading:
# enough context to cover an answer without drowning the LLM in text.
DEFAULT_K = 3


# --- Core retrieval -----------------------------------------------------------

def retrieve(question, k=DEFAULT_K, collection=None):
    """Return the k chunks most relevant to `question`.

    Args:
        question:   The query text (e.g. a student's interview question).
        k:          How many chunks to return (default 3).
        collection: Optional pre-opened ChromaDB collection. Pass this in a
                    long-running app (like Streamlit) so we don't reopen the
                    store on every call; leave it None for one-off scripts.

    Returns:
        A list of dicts, best match first:
            {
                "text":         the chunk's text,
                "chapter_name": which OSTEP chapter it came from,
                "page_number":  the page it was on,
                "distance":     ChromaDB distance (lower = more similar),
            }
    """
    if collection is None:
        collection = get_collection()

    results = collection.query(query_texts=[question], n_results=k)

    # ChromaDB returns each field as a list-of-lists (one inner list per query).
    # We only ever send one query, so we index [0] to get that query's results.
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        chunks.append(
            {
                "text": text,
                "chapter_name": metadata["chapter_name"],
                "page_number": metadata["page_number"],
                "distance": distance,
            }
        )
    return chunks


# --- Run directly to sanity-check retrieval -----------------------------------

if __name__ == "__main__":
    # Each question is paired with the chapter we EXPECT it to retrieve from.
    # This is the Step 2.3 acceptance check: known questions should pull back
    # chunks from the right chapter, proving semantic search actually works.
    test_cases = [
        ("How does the OS decide which process to run next?", "Scheduling Intro"),
        ("What is a virtual address space?", "Address Spaces"),
        ("Why can two threads deadlock?", "Concurrency Problems (Deadlocks)"),
    ]

    # Open the store once and reuse it across all test queries.
    collection = get_collection()
    print(f"Collection holds {collection.count()} chunks.\n")

    passed = 0
    for question, expected_chapter in test_cases:
        chunks = retrieve(question, collection=collection)
        top_chapter = chunks[0]["chapter_name"]
        ok = top_chapter == expected_chapter
        passed += ok

        print(f"Q: {question}")
        print(f"   expected chapter: {expected_chapter}")
        print(f"   top hit chapter : {top_chapter}  {'PASS' if ok else 'FAIL'}")
        for chunk in chunks:
            print(
                f"     - {chunk['chapter_name']} "
                f"(page {chunk['page_number']}, distance {chunk['distance']:.3f})"
            )
        print()

    print(f"Sanity check: {passed}/{len(test_cases)} questions hit the right chapter.")
