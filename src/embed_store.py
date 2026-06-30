"""
Embedding & storage module - turns the OSTEP chunks into vectors and stores
them in ChromaDB so we can search them later by meaning (not just keywords).

Pipeline:
    ingest.get_chunks()  ->  79 text chunks (+ metadata)
                         ->  embed each chunk with all-MiniLM-L6-v2
                         ->  store text + embedding + metadata in ChromaDB

This only needs to be run ONCE per document (or whenever the chunks change).
ChromaDB persists to the `chroma_db/` folder on disk, so the app and
retrieve.py can just open that folder later without re-embedding anything.

Run this file directly to (re)build the store and verify it:

    python src/embed_store.py
"""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Pull the chunks from our Step 2.1 module. Because this script lives in src/,
# running `python src/embed_store.py` puts src/ on the path, so `ingest` imports.
from ingest import get_chunks


# --- Configuration -----------------------------------------------------------

# Where ChromaDB keeps its data on disk. Resolved relative to THIS file so it
# always points at <project>/chroma_db regardless of where you run the script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# The name of our collection (think of it like a table inside the database).
COLLECTION_NAME = "ostep"

# The embedding model. all-MiniLM-L6-v2 is small (~80 MB), fast on CPU, and is
# ChromaDB's own default - a solid, battle-tested starting choice.
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


# --- Shared helpers (also imported by retrieve.py in Step 2.3) ---------------

def get_embedding_function():
    """Return the embedding function ChromaDB will use to turn text into
    vectors. Both storing (here) and querying (retrieve.py) MUST use the same
    one, or the vectors won't be comparable."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )


def get_collection():
    """Open the persistent ChromaDB collection, creating it if needed.
    retrieve.py imports this so it queries the exact same store + model."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


# --- Build the store: chunks -> embeddings -> ChromaDB ------------------------

def build_store():
    """(Re)build the ChromaDB collection from scratch and return it.

    We delete any existing collection first so re-running this never creates
    duplicate entries - you always end up with exactly the current chunks.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Start fresh: drop the old collection if it exists, then create a new one.
    # (get_or_create + add would stack duplicates on every run; this avoids that.)
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"Existing '{COLLECTION_NAME}' collection found - deleting it "
              f"so we can rebuild cleanly.")
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

    # Load the chunks from Step 2.1.
    chunks = get_chunks()

    # ChromaDB wants three parallel lists: ids, documents (the text), and
    # metadatas. We build them from our chunk dicts. The embedding function
    # turns each document into a vector automatically inside .add().
    ids = [f"chunk_{i:03d}" for i in range(len(chunks))]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "chapter_name": chunk["chapter_name"],
            "page_number": chunk["page_number"],
        }
        for chunk in chunks
    ]

    print(f"Embedding and storing {len(chunks)} chunks "
          f"(model: {EMBED_MODEL_NAME})...")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    print(f"Done. Collection '{COLLECTION_NAME}' now holds "
          f"{collection.count()} chunks at {CHROMA_DIR}.")
    return collection


# --- Run directly to build + verify -------------------------------------------

if __name__ == "__main__":
    collection = build_store()

    # Quick sanity check: ask a question and see which chapter comes back.
    # (Full retrieval lives in Step 2.3 / retrieve.py - this is just a smoke test
    # to confirm the store actually works end to end.)
    test_query = "What is a deadlock?"
    results = collection.query(query_texts=[test_query], n_results=3)

    print(f"\nSmoke test - query: {test_query!r}")
    print("Top 3 matches (chapter, page):")
    for metadata in results["metadatas"][0]:
        print(f"  - {metadata['chapter_name']} (page {metadata['page_number']})")
