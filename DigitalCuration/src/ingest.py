"""ingest.py

Utilities to collect files and extract text for indexing. This module is used by
the indexing pipeline to read supported file types and prepare Document objects
for the vector index.

Usage: generally invoked by `index_and_query.py` or run as a CLI script.
"""

from pathlib import Path
import os, sys, argparse
from typing import List
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ---------- defaults (override via CLI) ----------
DEFAULT_ROOT = Path("./data")
DEFAULT_PERSIST = Path("./storage")
ALLOW_EXT = {".txt", ".md", ".pdf", ".docx", ".csv", ".xlsx", ".py", ".m", ".yaml", ".yml"}
SKIP_EXT  = {".sldprt", ".sldasm", ".step", ".stp", ".iges", ".igs", ".stl", ".dwg", ".dxf", ".3mf", ".obj", ".zip", ".rar", ".exe"}
MAX_BYTES = 8 * 1024 * 1024  # 8 MB size cap to avoid giant binaries
MODEL_NAME = os.environ.get("LMSTUDIO_MODEL", "gpt-oss-20b")  # must match LM Studio
# -------------------------------------------------

# LLM + embeddings (LM Studio OpenAI-compatible API must be enabled)
Settings.llm = OpenAI(model=MODEL_NAME, temperature=0.2)
Settings.embed_model = HuggingFaceEmbedding("sentence-transformers/all-MiniLM-L6-v2")
Settings.chunk_size = 1200
Settings.chunk_overlap = 150

def read_text(fp: Path) -> str:
    """Best-effort text extractor for allowed extensions."""
    try:
        ext = fp.suffix.lower()
        if ext in {".txt", ".md", ".py", ".m", ".yaml", ".yml"}:
            return fp.read_text(encoding="utf-8", errors="ignore")
        if ext == ".csv":
            import pandas as pd
            df = pd.read_csv(fp, nrows=400)       # light sample
            return df.to_csv(index=False)
        if ext == ".xlsx":
            import pandas as pd
            df = pd.read_excel(fp, nrows=200)     # first sheet sample
            return df.to_csv(index=False)
        if ext == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(str(fp))
            return "\n\n".join((p.extract_text() or "") for p in r.pages)
        if ext == ".docx":
            from docx import Document as Docx
            d = Docx(str(fp))
            return "\n".join(p.text for p in d.paragraphs)
    except Exception:
        pass
    return ""  # fallback

def collect_files(root: Path, allow: set, skip: set, max_bytes: int) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in skip:      # skip CAD/binaries
            continue
        if ext not in allow: # only known texty types
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
        except Exception:
            pass
        files.append(p)
    return files

def main():
    ap = argparse.ArgumentParser(description="Ingest all subfolders under ROOT, build & persist vector index.")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="Folder to crawl (default: ./data)")
    ap.add_argument("--persist", default=str(DEFAULT_PERSIST), help="Persist dir (default: ./storage)")
    ap.add_argument("--dry-run", action="store_true", help="Only list eligible files; do not index")
    ap.add_argument("--max-bytes", type=int, default=MAX_BYTES, help=f"Size cap per file (default: {MAX_BYTES})")
    args = ap.parse_args()

    root = Path(args.root)
    persist_dir = Path(args.persist)
    root.mkdir(exist_ok=True)

    files = collect_files(root, ALLOW_EXT, SKIP_EXT, args.max_bytes)
    if args.dry_run:
        from collections import Counter
        c = Counter(p.suffix.lower() for p in files)
        print(f"[dry-run] Eligible files under {root.resolve()}: {len(files)}")
        for ext, n in sorted(c.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {ext or '<noext>'}: {n}")
        sys.exit(0)

    if not files:
        print(f"[ingest] No eligible files found under {root.resolve()}.")
        sys.exit(0)

    print(f"[ingest] Found {len(files)} files. Reading & embedding…")
    docs: List[Document] = []
    for fp in files:
        text = read_text(fp)
        if not text.strip():
            continue
        md = {
            "file_name": fp.name,
            "file_path": str(fp.resolve()),
            "rel_path": str(fp.relative_to(root)),
        }
        docs.append(Document(text=text, metadata=md))

    if not docs:
        print("[ingest] No readable text extracted. (Files may be binary/CAD only.)")
        sys.exit(0)

    index = VectorStoreIndex.from_documents(docs)
    index.storage_context.persist(persist_dir=str(persist_dir))
    print(f"[ingest] Indexed {len(docs)} docs; persisted to {persist_dir.resolve()}")

if __name__ == "__main__":
    main()
