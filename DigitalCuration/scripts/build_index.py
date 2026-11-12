"""scripts/build_index.py

Build the nearest-neighbors search index used by the Streamlit app
(`scripts/streamlit_search.py`) and `scripts/query_index.py`.

One entry is created per ESMS metadata YAML under `./metadata` (its text is the
YAML plus an excerpt of the matching raw file in `./data`), plus one entry per
raw file in `./data` that has no metadata YAML.

Writes to `./storage`:
    meta.json       list of {"source": <relative path>}
    embeddings.npy  normalized sentence-transformers embeddings
    nbrs.pkl        fitted sklearn NearestNeighbors (cosine metric)

Usage (from the repository root):
    python scripts/build_index.py

Environment:
    SAMPLE_LIMIT    index only the first N entries (quick test)
    RAW_CHARS       max characters taken from each raw file (default 4000)
"""

import json
import logging
import os
import pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

DATA_DIR = Path("data")
META_DIR = Path("metadata")
PERSIST_DIR = Path("storage")
MODEL_NAME = "all-MiniLM-L6-v2"
RAW_CHARS = int(os.environ.get("RAW_CHARS", "4000"))
MAX_BYTES = 8 * 1024 * 1024

logging.getLogger("pypdf").setLevel(logging.ERROR)  # silence noisy font warnings

TEXT_EXT = {".txt", ".md", ".py", ".m", ".yaml", ".yml", ".json"}


def read_raw_text(fp: Path) -> str:
    """Best-effort text extraction; returns '' for unsupported/binary files."""
    try:
        if fp.stat().st_size > MAX_BYTES:
            return ""
        ext = fp.suffix.lower()
        if ext in TEXT_EXT:
            return fp.read_text(encoding="utf-8", errors="ignore")
        if ext == ".csv":
            import pandas as pd
            return pd.read_csv(fp, nrows=200).to_csv(index=False)
        if ext == ".xlsx":
            import pandas as pd
            return pd.read_excel(fp, nrows=200).to_csv(index=False)
        if ext == ".pdf":
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(str(fp)).pages[:20])
        if ext == ".docx":
            from docx import Document
            return "\n".join(p.text for p in Document(str(fp)).paragraphs)
    except Exception as e:
        print(f"  (could not read {fp}: {e})")
    return ""


def raw_for_yaml(yaml_path: Path):
    """metadata/data/X/foo.yaml -> data/X/foo.<ext> if it exists."""
    rel = yaml_path.relative_to(META_DIR)
    if rel.parts and rel.parts[0] == "data":
        rel = Path(*rel.parts[1:])
    parent = DATA_DIR / rel.parent
    if parent.is_dir():
        for cand in parent.iterdir():
            if cand.is_file() and cand.stem == yaml_path.stem:
                return cand
    return None


def gather_entries():
    entries = []
    covered = set()
    for yp in sorted(META_DIR.rglob("*.y*ml")):
        text = yp.read_text(encoding="utf-8", errors="ignore")
        raw = raw_for_yaml(yp)
        if raw is not None:
            covered.add(raw.resolve())
            text += "\n\n" + read_raw_text(raw)[:RAW_CHARS]
        if text.strip():
            entries.append({"source": str(yp), "text": text})

    for fp in sorted(DATA_DIR.rglob("*")):
        if not fp.is_file() or fp.name.startswith(".") or fp.resolve() in covered:
            continue
        text = read_raw_text(fp)[:RAW_CHARS]
        # still index the file name so non-text files remain findable
        text = f"{fp.name}\n{fp.parent}\n{text}"
        entries.append({"source": str(fp), "text": text})
    return entries


def main():
    entries = gather_entries()
    limit = int(os.environ.get("SAMPLE_LIMIT", "0") or 0)
    if limit > 0:
        entries = entries[:limit]
    if not entries:
        raise SystemExit("No documents found in ./metadata or ./data.")

    n_yaml = sum(e["source"].endswith((".yaml", ".yml")) for e in entries)
    print(f"Indexing {len(entries)} entries ({n_yaml} metadata YAMLs, {len(entries) - n_yaml} raw files)...")

    model = SentenceTransformer(MODEL_NAME)
    embs = model.encode([e["text"] for e in entries], batch_size=32,
                        show_progress_bar=True, normalize_embeddings=True)
    embs = np.asarray(embs, dtype=np.float32)

    nbrs = NearestNeighbors(metric="cosine").fit(embs)

    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    (PERSIST_DIR / "meta.json").write_text(
        json.dumps([{"source": e["source"]} for e in entries], indent=1), encoding="utf-8")
    np.save(PERSIST_DIR / "embeddings.npy", embs)
    with open(PERSIST_DIR / "nbrs.pkl", "wb") as f:
        pickle.dump(nbrs, f)
    print(f"Done. Index written to {PERSIST_DIR}/ (meta.json, embeddings.npy, nbrs.pkl)")


if __name__ == "__main__":
    main()
