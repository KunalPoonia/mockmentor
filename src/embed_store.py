"""
Embedding & storage module - turns a subject's chunks into vectors and stores
them in ChromaDB so we can search them later by meaning (not just keywords).

Multi-subject: each subject gets its OWN ChromaDB collection (name from
ingest.SUBJECT_CORPORA), so subjects stay isolated and adding one never
disturbs another. Every chunk also carries a `subject` metadata field.

Pipeline (per subject):
    ingest.get_chunks(subject) -> chunks (+ metadata)
                               -> embed each with all-MiniLM-L6-v2
                               -> store text + embedding + metadata in ChromaDB

Run once per subject (or when its notes change). ChromaDB persists to
`chroma_db/` on disk.

    python src/embed_store.py            # (re)build ALL subjects
    python src/embed_store.py os         # just OSTEP
    python src/embed_store.py dsa        # just DSA
"""

import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from ingest import get_chunks, get_collection_name, list_subject_ids


# --- Configuration -----------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# all-MiniLM-L6-v2: small (~80 MB), fast on CPU, ChromaDB's default. Storing and
# querying MUST use the same model or the vectors aren't comparable.
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


# --- Shared helpers (also imported by retrieve.py) ---------------------------

def get_embedding_function():
    """The embedding function ChromaDB uses to turn text into vectors."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )


def get_collection(subject_id="os"):
    """Open the persistent ChromaDB collection for a subject, creating it if
    needed. retrieve.py imports this so it queries the same store + model."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=get_collection_name(subject_id),
        embedding_function=get_embedding_function(),
    )


# --- Build a subject's store: chunks -> embeddings -> ChromaDB ----------------

def build_store(subject_id="os"):
    """(Re)build one subject's ChromaDB collection from scratch and return it.

    Drops the existing collection first so re-running never stacks duplicates.
    `page_number` is only stored when present (OSTEP has it; DSA topics don't) -
    ChromaDB rejects None metadata values, so we omit the key entirely instead.
    """
    collection_name = get_collection_name(subject_id)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        print(f"Existing '{collection_name}' collection found - deleting it "
              f"so we can rebuild cleanly.")
        client.delete_collection(collection_name)

    collection = client.create_collection(
        name=collection_name,
        embedding_function=get_embedding_function(),
    )

    chunks = get_chunks(subject_id)

    ids = [f"{subject_id}_chunk_{i:03d}" for i in range(len(chunks))]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = []
    for chunk in chunks:
        meta = {"subject": subject_id, "chapter_name": chunk["chapter_name"]}
        if "page_number" in chunk:            # OSTEP has pages; DSA topics don't
            meta["page_number"] = chunk["page_number"]
        metadatas.append(meta)

    print(f"[{subject_id}] Embedding and storing {len(chunks)} chunks "
          f"(model: {EMBED_MODEL_NAME})...")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    print(f"[{subject_id}] Done. Collection '{collection_name}' now holds "
          f"{collection.count()} chunks at {CHROMA_DIR}.")
    return collection


def build_all():
    """(Re)build every subject that has a corpus defined in ingest.py."""
    for subject_id in list_subject_ids():
        build_store(subject_id)
        print()


# --- Run directly to build + verify -------------------------------------------

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target is None:
        build_all()
        subjects_to_test = list_subject_ids()
    else:
        build_store(target)
        subjects_to_test = [target]

    # Smoke test each built subject with a representative query.
    smoke = {"os": "What is a deadlock?", "dsa": "When would you use a sliding window?"}
    for subject_id in subjects_to_test:
        query = smoke.get(subject_id, "introduction")
        collection = get_collection(subject_id)
        results = collection.query(query_texts=[query], n_results=3)
        print(f"\n[{subject_id}] Smoke test - query: {query!r}")
        print("Top 3 matches (section):")
        for metadata in results["metadatas"][0]:
            page = f" (page {metadata['page_number']})" if "page_number" in metadata else ""
            print(f"  - {metadata['chapter_name']}{page}")
