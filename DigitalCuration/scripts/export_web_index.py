"""scripts/export_web_index.py

Build a browser-ready semantic search index for the ECLIPSE web page.

For every artifact in the data library it gathers:
  * the ESMS metadata YAML (title, description, keywords, all text fields),
  * a text excerpt of the file itself (when the format is readable),
and embeds them with the same model used by the rest of digitalCuration
(sentence-transformers/all-MiniLM-L6-v2, normalized). The result is a single
JSON file that ScenarioIndex.html loads; the page embeds the user's query in
the browser with the same model (transformers.js) and ranks by cosine.
A copy wrapped as JavaScript (search_index.js) is written next to it so the
page also works when opened directly from disk (file://).

Each document gets two vectors (metadata + file content); the page scores a
document by the best of the two.

Usage (from the DigitalCuration folder):
    .venv/bin/python scripts/export_web_index.py
    .venv/bin/python scripts/export_web_index.py --data-dir ./data --meta-dir ./metadata/data --out ./web/search_index.json

To search another library later, point --data-dir / --meta-dir to it.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TEXT_EXT = {".txt", ".md", ".py", ".m", ".yaml", ".yml", ".json"}
SKIP_KEYS = {"file_path", "rel_path", "file_name", "access_control", "access control"}
NOISE_VALUES = {"not applicable", "n/a", "na", "tbd", "none", "public", "unknown", "-", ""}
CONTENT_CHARS = 2000
SUMMARY_CHARS = 400
MAX_KEYWORDS = 12

logging.getLogger("pypdf").setLevel(logging.ERROR)  # silence font-encoding chatter


# --------------------------------------------------------------------------- #
# File text extraction (same formats as src/ingest.py)
# --------------------------------------------------------------------------- #
def read_text(fp: Path) -> str:
    ext = fp.suffix.lower()
    try:
        if ext in TEXT_EXT:
            return fp.read_text(encoding="utf-8", errors="ignore")
        if ext == ".csv":
            import pandas as pd
            return pd.read_csv(fp, nrows=200).to_csv(index=False)
        if ext == ".xlsx":
            import pandas as pd
            return pd.read_excel(fp, nrows=100).to_csv(index=False)
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(fp))
            out = []
            for page in reader.pages[:5]:
                out.append(page.extract_text() or "")
                if sum(map(len, out)) > CONTENT_CHARS * 2:
                    break
            return "\n".join(out)
        if ext == ".docx":
            from docx import Document as Docx
            return "\n".join(p.text for p in Docx(str(fp)).paragraphs)
    except Exception as exc:  # unreadable file: metadata alone will be used
        print(f"  ! could not read {fp.name}: {exc}", file=sys.stderr)
    return ""


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


# --------------------------------------------------------------------------- #
# ESMS YAML walking (handles both ESMS layouts present in metadata/)
# --------------------------------------------------------------------------- #
def norm_key(k) -> str:
    return str(k).strip().lower().replace("-", "_")


def walk(node, key_path=()):
    """Yield (key_path, string) for every leaf string in a YAML tree."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, key_path + (norm_key(k),))
    elif isinstance(node, list):
        for item in node:
            yield from walk(item, key_path + ("[]",))
    elif node is not None and not isinstance(node, bool):
        yield key_path, str(node)


def extract_metadata(meta: dict) -> dict:
    summary, texts, keywords = "", [], []
    seen_text, seen_kw = set(), set()
    for path, value in walk(meta):
        named = [k for k in path if k != "[]"]
        last = named[-1] if named else ""
        if last in SKIP_KEYS or last.startswith("reference"):
            continue
        value = clean(value)
        if value.lower() in NOISE_VALUES:
            continue
        if not summary and "description" in last and len(value) > 20:
            summary = value
        if value.lower() not in seen_text:
            seen_text.add(value.lower())
            texts.append(value)
        # short values held in lists (domains, methods, focus areas...) make good tags
        if path and path[-1] == "[]" and 2 < len(value) <= 40 and value.lower() not in seen_kw:
            seen_kw.add(value.lower())
            keywords.append(value)
    if len(summary) > SUMMARY_CHARS:
        summary = summary[: SUMMARY_CHARS - 1].rsplit(" ", 1)[0] + "…"
    return {"summary": summary, "text": " ".join(texts), "keywords": keywords[:MAX_KEYWORDS]}


# --------------------------------------------------------------------------- #
# Library discovery
# --------------------------------------------------------------------------- #
def find_data_file(meta_file: Path, meta: dict, meta_dir: Path, data_dir: Path) -> Path | None:
    """metadata/data/<sub>/<stem>.yaml  <->  data/<sub>/<file_name>."""
    sub = meta_file.parent.relative_to(meta_dir)
    name = meta.get("file_name")
    if name:
        cand = data_dir / sub / name
        if cand.exists():
            return cand
    matches = sorted((data_dir / sub).glob(meta_file.stem + ".*"))
    return matches[0] if matches else None


def collect(data_dir: Path, meta_dir: Path) -> list[dict]:
    docs, used = [], set()
    for meta_file in sorted(meta_dir.rglob("*.y*ml")):
        try:
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8", errors="ignore")) or {}
        except yaml.YAMLError as exc:
            print(f"  ! bad YAML {meta_file}: {exc}", file=sys.stderr)
            continue
        if not isinstance(meta, dict):
            continue
        data_file = find_data_file(meta_file, meta, meta_dir, data_dir)
        if data_file:
            used.add(data_file.resolve())
        docs.append({"meta_file": meta_file, "meta": meta, "data_file": data_file})

    # artifacts that have no metadata yet are still searchable through their content
    for fp in sorted(data_dir.rglob("*")):
        if fp.is_file() and fp.resolve() not in used and not fp.name.startswith((".", "~$")):
            docs.append({"meta_file": None, "meta": {}, "data_file": fp})
    return docs


# --------------------------------------------------------------------------- #
def main() -> None:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=str(root / "data"))
    ap.add_argument("--meta-dir", default=str(root / "metadata" / "data"))
    ap.add_argument("--out", default=str(root / "web" / "search_index.json"))
    ap.add_argument("--base", default=str(root),
                    help="Paths in the index are written relative to this folder (default: DigitalCuration/)")
    args = ap.parse_args()

    data_dir, meta_dir, out = Path(args.data_dir).resolve(), Path(args.meta_dir).resolve(), Path(args.out).resolve()
    base = Path(args.base).resolve()

    def rel(p: Path | None) -> str | None:
        if p is None:
            return None
        try:
            return p.resolve().relative_to(base).as_posix()
        except ValueError:
            return p.resolve().as_posix()

    print(f"Collecting artifacts from {data_dir} (metadata: {meta_dir})")
    raw = collect(data_dir, meta_dir)

    documents, meta_texts, content_texts = [], [], []
    for item in raw:
        meta, data_file, meta_file = item["meta"], item["data_file"], item["meta_file"]
        info = extract_metadata(meta)
        name = (data_file.name if data_file else meta.get("file_name")) or meta_file.stem
        title = clean(str(meta.get("title") or Path(name).stem))
        folder_src = data_file.parent.relative_to(data_dir) if data_file else meta_file.parent.relative_to(meta_dir)
        folder = "" if str(folder_src) == "." else folder_src.as_posix()
        content = clean(read_text(data_file))[:CONTENT_CHARS] if data_file else ""

        documents.append({
            "id": len(documents),
            "title": title,
            "file": name,
            "type": Path(name).suffix.lstrip(".").lower(),
            "folder": folder,
            "summary": info["summary"] or content[:200],
            "keywords": info["keywords"],
            "path": rel(data_file),
            "metadata_path": rel(meta_file),
            "excerpt": content[:300],
        })
        # Title first: MiniLM truncates long inputs (~256 tokens)
        head = f"{title}. {folder.replace('/', ' ')}. {info['summary']} {' , '.join(info['keywords'])}"
        meta_texts.append(clean(f"{head} {info['text']}"))
        content_texts.append(clean(f"{title}. {content}") if content else "")

    print(f"Embedding {len(documents)} documents with {MODEL_NAME} …")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    meta_emb = model.encode(meta_texts, normalize_embeddings=True, batch_size=32, show_progress_bar=True)
    has_content = [i for i, t in enumerate(content_texts) if t]
    content_emb = model.encode([content_texts[i] for i in has_content], normalize_embeddings=True,
                               batch_size=32, show_progress_bar=True) if has_content else []

    round4 = lambda v: [round(float(x), 4) for x in v]
    for i, doc in enumerate(documents):
        doc["vectors"] = [round4(meta_emb[i])]
    for j, i in enumerate(has_content):
        documents[i]["vectors"].append(round4(content_emb[j]))

    payload = {
        "model": MODEL_NAME,
        "browser_model": "Xenova/all-MiniLM-L6-v2",
        "dim": int(meta_emb.shape[1]),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(documents),
        "documents": documents,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    out.write_text(data, encoding="utf-8")
    # Same index wrapped in a script: browsers block fetch() on file:// pages but
    # allow <script src>, so ScenarioIndex.html also works when opened by double-click.
    out_js = out.with_suffix(".js")
    out_js.write_text("window.DC_SEARCH_INDEX=" + data + ";\n", encoding="utf-8")
    print(f"Wrote {out} and {out_js.name} ({out.stat().st_size / 1e6:.2f} MB, {len(documents)} documents)")


if __name__ == "__main__":
    main()
