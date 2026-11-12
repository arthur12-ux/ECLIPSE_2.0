"""scripts/export_web_index.py

Export the Digital Curation search index for the ECLIPSE web page
(ScenarioIndex.html → Mission Scenario → "Search the model library").

The index is built with exactly the same logic as the Streamlit app's index
(`scripts/build_index.py`): same entries (one per ESMS metadata YAML, plus one per
raw file without metadata), same text per entry, same model
(all-MiniLM-L6-v2), same normalized embeddings. The page embeds the query with
the same model in the browser (transformers.js, full-precision weights) and
scores with cosine similarity, i.e. the `1 - cosine distance` score shown by
`scripts/streamlit_search.py`. Rankings and scores therefore match the
Streamlit app (to ~±0.001).

Only display fields (title, summary, tags, links) are added on top; they do not
affect ranking.

Outputs (in web/):
    search_index.json   the index
    search_index.js     same data as `window.DC_SEARCH_INDEX=...;` so the page
                        also works when opened from disk (file://), where
                        browsers block fetch() but allow <script src>.

Usage (from anywhere):
    .venv/bin/python scripts/export_web_index.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent  # DigitalCuration/
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_index as bi  # noqa: E402  (the Streamlit index builder: single source of truth)

SUMMARY_CHARS = 400
MAX_KEYWORDS = 12
SKIP_KEYS = {"file_path", "rel_path", "file_name", "access_control", "access control"}
NOISE_VALUES = {"not applicable", "n/a", "na", "tbd", "none", "public", "unknown", "-", ""}


# --------------------------------------------------------------------------- #
# Display-only helpers (do not influence ranking)
# --------------------------------------------------------------------------- #
def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def walk(node, key_path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, key_path + (str(k).strip().lower().replace("-", "_"),))
    elif isinstance(node, list):
        for item in node:
            yield from walk(item, key_path + ("[]",))
    elif node is not None and not isinstance(node, bool):
        yield key_path, str(node)


def display_fields(meta: dict) -> tuple[str, list[str]]:
    """First description found + short list values usable as tags."""
    summary, keywords, seen = "", [], set()
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
        if path and path[-1] == "[]" and 2 < len(value) <= 40 and value.lower() not in seen:
            seen.add(value.lower())
            keywords.append(value)
    if len(summary) > SUMMARY_CHARS:
        summary = summary[: SUMMARY_CHARS - 1].rsplit(" ", 1)[0] + "…"
    return summary, keywords[:MAX_KEYWORDS]


def describe(entry: dict) -> dict:
    """Display info for one build_index entry, mirroring streamlit_search.py."""
    src = Path(entry["source"])
    is_yaml = src.suffix.lower() in (".yaml", ".yml")
    raw = bi.raw_for_yaml(src) if is_yaml else src
    meta = {}
    if is_yaml:
        try:
            meta = yaml.safe_load(src.read_text(encoding="utf-8", errors="ignore")) or {}
        except yaml.YAMLError:
            meta = {}
        if not isinstance(meta, dict):
            meta = {}
    shown = raw if raw is not None else src
    # Same title precedence as the Streamlit app
    title = meta.get("model_title") or meta.get("title") or meta.get("file_name") or shown.name
    summary, keywords = display_fields(meta)
    try:
        folder = shown.parent.relative_to(bi.DATA_DIR).as_posix()
    except ValueError:
        folder = shown.parent.as_posix()
    excerpt = ""
    if not summary and raw is not None:
        excerpt = clean(bi.read_raw_text(raw))[:200]
    return {
        "title": clean(str(title)),
        "file": shown.name,
        "type": shown.suffix.lstrip(".").lower(),
        "folder": "" if folder == "." else folder,
        "summary": summary or excerpt,
        "keywords": keywords,
        "path": raw.as_posix() if raw is not None else None,
        "metadata_path": src.as_posix() if is_yaml else None,
        "source": src.as_posix(),
    }


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "web" / "search_index.json"))
    args = ap.parse_args()
    out = Path(args.out).resolve()

    # build_index.py uses paths relative to the DigitalCuration folder
    os.chdir(ROOT)

    entries = bi.gather_entries()
    if not entries:
        raise SystemExit("No documents found in ./metadata or ./data.")
    print(f"Indexing {len(entries)} entries exactly like scripts/build_index.py …")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(bi.MODEL_NAME)
    embs = model.encode([e["text"] for e in entries], batch_size=32,
                        show_progress_bar=True, normalize_embeddings=True)

    documents = []
    for i, (entry, vec) in enumerate(zip(entries, embs)):
        doc = {"id": i, **describe(entry)}
        doc["vector"] = [round(float(x), 5) for x in vec]
        documents.append(doc)

    payload = {
        "model": f"sentence-transformers/{bi.MODEL_NAME}",
        "browser_model": f"Xenova/{bi.MODEL_NAME}",
        "browser_quantized": False,  # full-precision weights → same vectors as Python
        "scoring": "cosine similarity (= 1 - cosine distance, as in streamlit_search.py)",
        "dim": int(embs.shape[1]),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(documents),
        "documents": documents,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    out.write_text(data, encoding="utf-8")
    out.with_suffix(".js").write_text("window.DC_SEARCH_INDEX=" + data + ";\n", encoding="utf-8")
    print(f"Wrote {out} and {out.with_suffix('.js').name} ({out.stat().st_size / 1e6:.2f} MB, {len(documents)} entries)")


if __name__ == "__main__":
    main()
