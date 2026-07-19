"""
Integration tests for retrieve.py.

These query the real ChromaDB collections, so they require the stores to be
built first:  python src/embed_store.py   (builds OS + DSA).
They load the local embedding model but do NOT need Ollama (no grading here).

Roadmap check covered: "retrieval returns the right section for a known
question" - for both subjects, proving the multi-subject pipeline works.
"""

import pytest

from embed_store import get_collection
from ingest import get_collection_name
from retrieve import retrieve


def _collection_or_skip(subject):
    """Open a subject's collection, or skip the test if it's empty/missing
    (i.e. the user hasn't run embed_store.py yet)."""
    try:
        col = get_collection(subject)
    except Exception as exc:  # noqa: BLE001 - surface as a skip, not an error
        pytest.skip(f"Could not open '{subject}' collection: {exc}")
    if col.count() == 0:
        pytest.skip(f"'{subject}' collection is empty - run: python src/embed_store.py")
    return col


def test_collections_are_named_per_subject():
    assert get_collection_name("os") == "ostep"
    assert get_collection_name("dsa") == "dsa"


def test_retrieve_returns_k_chunks_with_required_keys():
    col = _collection_or_skip("os")
    chunks = retrieve("What is a deadlock?", k=3, collection=col, subject="os")
    assert len(chunks) == 3
    for c in chunks:
        assert "text" in c and c["text"]
        assert "chapter_name" in c
        assert "distance" in c


def test_os_known_question_hits_expected_chapter_in_top_k():
    col = _collection_or_skip("os")
    chunks = retrieve("What is a deadlock, and what conditions cause it?",
                      k=3, collection=col, subject="os")
    sections = [c["chapter_name"] for c in chunks]
    assert "Concurrency Problems (Deadlocks)" in sections


def test_dsa_known_question_hits_expected_topic_in_top_k():
    col = _collection_or_skip("dsa")
    chunks = retrieve("When would you use a sliding window?",
                      k=3, collection=col, subject="dsa")
    sections = [c["chapter_name"] for c in chunks]
    assert "Sliding Window" in sections


def test_os_chunks_carry_page_numbers():
    col = _collection_or_skip("os")
    chunks = retrieve("virtual address space", k=3, collection=col, subject="os")
    assert all("page_number" in c for c in chunks)


def test_dsa_chunks_have_no_page_numbers():
    col = _collection_or_skip("dsa")
    chunks = retrieve("how does binary search work", k=3, collection=col, subject="dsa")
    assert all("page_number" not in c for c in chunks)
