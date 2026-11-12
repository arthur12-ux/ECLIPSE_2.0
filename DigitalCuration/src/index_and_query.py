"""index_and_query.py

Build and persist a semantic index over `./data` and `./metadata` using llama-index
and a local sentence-transformers embedding adapter.

Usage:
    python index_and_query.py

Environment:
    Ensure required packages in `requirements.txt` are installed; optional env flags: SAMPLE_LIMIT, SHOW_PROGRESS.
"""

import os
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer

from llama_index.core import Document, VectorStoreIndex, Settings, StorageContext, load_index_from_storage, ServiceContext

# Configuration
DATA_DIR = Path("./data")
META_DIR = Path("./metadata")
PERSIST_DIR = Path("./storage")
PERSIST_DIR.mkdir(parents=True, exist_ok=True)


def gather_text_documents():
    docs = []
    for fp in DATA_DIR.rglob("*"):
        if not fp.is_file():
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        if not text.strip():
            continue
        docs.append({"text": text, "source": str(fp)})

    for fp in META_DIR.rglob("*.yaml"):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        if not text.strip():
            continue
        docs.append({"text": text, "source": str(fp)})

    return docs


class LocalHFEmbedding:
    """A small embedding adapter that uses sentence-transformers but exposes the
    methods expected by llama-index (embed_documents, embed_query).
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        # return list[list[float]]
        # honor SHOW_PROGRESS environment variable for a status bar during encoding
        show_pb = os.environ.get("SHOW_PROGRESS", "0") == "1"
        batch_size = int(os.environ.get("EMB_BATCH_SIZE", "32"))
        embs = self.model.encode(texts, show_progress_bar=show_pb, batch_size=batch_size)
        return [list(map(float, e)) for e in embs]

    def embed_query(self, text):
        emb = self.model.encode([text])[0]
        return list(map(float, emb))


def main():
    docs = gather_text_documents()
    if not docs:
        print("No documents found to index.")
        raise SystemExit(1)

    # Optional sample limit for quick testing
    sample_limit = int(os.environ.get("SAMPLE_LIMIT", "0") or 0)
    if sample_limit > 0:
        print(f"SAMPLE_LIMIT set: only indexing first {sample_limit} documents")
        docs = docs[:sample_limit]

    print(f"Preparing {len(docs)} documents for indexing...")
    # Prepare llama-index Documents
    li_docs = [Document(text=d["text"], metadata={"source": d["source"]}) for d in docs]

    # Use our local embedding adapter with llama-index Settings
    embed_adapter = LocalHFEmbedding()
    try:
        Settings.embed_model = embed_adapter
    except Exception:
        # older/newer llama-index variations may expect different configuration; assign if present
        try:
            from llama_index import ServiceContext
            from llama_index import LLMPredictor
            # best-effort: create a ServiceContext with our embedder
            sc = ServiceContext.from_defaults(embed_model=embed_adapter)
            index = VectorStoreIndex.from_documents(li_docs, service_context=sc)
        except Exception:
            # fallback to direct assignment if ServiceContext isn't available
            pass

    # Build index with llama-index
    index = VectorStoreIndex.from_documents(li_docs)
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
    print(f"Llama-index built and persisted to {PERSIST_DIR}")

    # Load index and serve queries
    storage = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
    index = load_index_from_storage(storage)
    print("Index loaded. Enter a natural language query (or 'exit'):")
    while True:
        q = input("> ")
        if not q.strip():
            continue
        if q.strip().lower() in ("exit", "quit"):
            break
        response = index.as_query_engine().query(q)
        print("---\n", response, "\n---")


if __name__ == '__main__':
    main()
