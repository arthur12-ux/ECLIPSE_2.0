"""prototype/ingest.py

Prototype ingestion utilities (experimental). This module contains a richer
ingestion pipeline used during development and experimentation. It is a
work-in-progress and kept under `prototype/`.
"""

# ingest_build_index.py
from pathlib import Path
import os, sys, argparse
from typing import List, Dict, Any, Optional
import hashlib
import json
import mimetypes
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    _HUGGINGFACE_AVAILABLE = True
except Exception:
    HuggingFaceEmbedding = None  # type: ignore
    _HUGGINGFACE_AVAILABLE = False

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
if _HUGGINGFACE_AVAILABLE and HuggingFaceEmbedding is not None:
    try:
        Settings.embed_model = HuggingFaceEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        Settings.embed_model = None
else:
    Settings.embed_model = None
Settings.chunk_size = 1200
Settings.chunk_overlap = 150

def read_text(fp: Path, verbose: bool = False) -> str:
    """Best-effort text extractor for allowed extensions.

    If verbose is True, exceptions encountered while attempting to read a file
    will be printed so you can debug problematic files.
    """
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
    except Exception as e:
        if verbose:
            print(f"[read_text] Failed to read {fp}: {type(e).__name__}: {e}")
    return ""  # fallback


def compute_sha256(fp: Path) -> str:
    h = hashlib.sha256()
    try:
        with fp.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def load_sidecar(fp: Path) -> Optional[Dict[str, Any]]:
    # look for {stem}.yaml/.yml/.json next to the file
    for ext in (".yaml", ".yml", ".json"):
        cand = fp.with_suffix(ext)
        if cand.exists():
            try:
                text = cand.read_text(encoding="utf-8", errors="ignore")
                if ext == ".json":
                    return json.loads(text)
                else:
                    try:
                        import yaml
                    except Exception:
                        return None
                    return yaml.safe_load(text) or {}
            except Exception:
                return None
    return None


def load_esms_vocab(vocab_dir: Path) -> Dict[str, List[str]]:
    """Load YAML files from vocab dir and return mapping category->terms list.

    Heuristic: file name containing a category name maps the file to that category.
    We flatten keys and string leaf values as candidate terms.
    """
    out: Dict[str, List[str]] = {}
    if not vocab_dir or not vocab_dir.exists():
        return out
    try:
        import yaml
    except Exception:
        print("[esms] PyYAML not installed; ESMS vocab loading disabled. Install pyyaml to enable.")
        return out

    for p in vocab_dir.iterdir():
        if not p.is_file() or p.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        key = p.stem.lower()
        # pick category name by filename hints
        category = None
        for cat in ("identity", "scope", "representation", "utility", "assessment", "lifecycle"):
            if cat in key:
                category = cat
                break
        if category is None:
            category = key
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(raw) if p.suffix.lower() == ".json" else yaml.safe_load(raw)
        except Exception:
            continue

        terms: List[str] = []

        def walk(v):
            if v is None:
                return
            if isinstance(v, str):
                s = v.strip()
                if s:
                    terms.append(s)
            elif isinstance(v, dict):
                for k, vv in v.items():
                    walk(k)
                    walk(vv)
            elif isinstance(v, list):
                for item in v:
                    walk(item)

        walk(data)
        # deduplicate and store
        uniq = []
        seen = set()
        for t in terms:
            tl = t.lower()
            if tl in seen:
                continue
            seen.add(tl)
            uniq.append(t)
        out.setdefault(category, []).extend(uniq)
    return out


def match_esms_terms(sample: str, vocab: Dict[str, List[str]], mode: str = "heuristic") -> Dict[str, List[str]]:
    """Return matched terms grouped by category. Mode supports 'exact' and 'heuristic'.

    heuristic: case-insensitive substring match of vocab term in sample.
    exact: exact token match against whitespace-separated tokens.
    """
    matches: Dict[str, List[str]] = {}
    if not vocab:
        return matches
    s = sample.lower()
    tokens = set(s.split())
    for cat, terms in vocab.items():
        for t in terms:
            tl = t.lower()
            if mode == "exact":
                if tl in tokens:
                    matches.setdefault(cat, []).append(t)
            else:  # heuristic
                if tl and tl in s:
                    matches.setdefault(cat, []).append(t)
    return matches


def build_metadata(fp: Path, text: str, root: Path, args: argparse.Namespace, sidecar: Optional[Dict[str, Any]] = None, vocab_matches: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    md: Dict[str, Any] = {}
    try:
        rel = str(fp.relative_to(root))
    except Exception:
        rel = str(fp)
    md["file_name"] = fp.name
    md["file_path"] = str(fp.resolve())
    md["rel_path"] = rel
    md["title"] = (sidecar.get("title") if sidecar and isinstance(sidecar, dict) and sidecar.get("title") else fp.stem)
    desc = "".join(text.splitlines(True)[:10]).strip()
    if not desc:
        desc = (text or "")[:500]
    md["description"] = desc[:1000]
    try:
        md["file_size_bytes"] = fp.stat().st_size
    except Exception:
        md["file_size_bytes"] = None
    md["mime_type"] = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
    if args.checksum:
        md["checksum_sha256"] = compute_sha256(fp)

    # start esms block
    esms = {}
    # merge sidecar esms if present (sidecar authoritative)
    if sidecar and isinstance(sidecar, dict):
        sc_esms = sidecar.get("esms") or {}
        if isinstance(sc_esms, dict):
            esms.update(sc_esms)

    # merge vocab matches into esms under 'vocab_matches'
    if vocab_matches:
        esms.setdefault("vocab_matches", {}).update(vocab_matches)

    md["esms"] = esms
    # include raw sidecar copy so nothing is lost
    if sidecar:
        md["sidecar"] = sidecar
    return md


def check_env() -> None:
    """Print which optional/required libraries for file readers are available."""
    pkgs = {
        "pandas": "pandas",
        "openpyxl (xlsx)": "openpyxl",
        "pypdf (pdf)": "pypdf",
        "python-docx (docx)": "python-docx",
        "tqdm (progress bar)": "tqdm",
    }
    print("Environment check:")
    for name, mod in pkgs.items():
        try:
            __import__(mod)
            print(f"  OK: {name}")
        except Exception:
            print(f"  MISSING: {name}")

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

def load_yaml_template(template_path: Path) -> dict:
    """Load a YAML template and return its structure as a dict."""
    try:
        import yaml
        raw = template_path.read_text(encoding="utf-8", errors="ignore")
        return yaml.safe_load(raw)
    except Exception as e:
        print(f"[esms] Failed to load template {template_path}: {e}")
        return {}

def main():
    ap = argparse.ArgumentParser(description="Ingest all subfolders under ROOT, build & persist vector index.")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="Folder to crawl (default: ./data)")
    ap.add_argument("--persist", default=str(DEFAULT_PERSIST), help="Persist dir (default: ./storage)")
    ap.add_argument("--dry-run", action="store_true", help="Only list eligible files; do not index")
    ap.add_argument("--verbose", action="store_true", help="Print verbose read errors and diagnostics")
    ap.add_argument("--checksum", action="store_true", help="Compute sha256 checksum for each file and include in metadata")
    ap.add_argument("--use-sidecar", action="store_true", help="Load adjacent .yaml/.yml/.json sidecar metadata if present and merge into metadata")
    ap.add_argument("--esms-vocab-dir", default=None, help="Directory containing ESMS YAML vocab files")
    ap.add_argument("--esms-match-mode", choices=["exact","heuristic"], default="heuristic", help="Matching mode to use for ESMS vocab (default: heuristic)")
    ap.add_argument("--out-meta-dir", default=str(Path("./metadata")), help="Directory to write per-file metadata YAML and combined metadata.jsonl")
    ap.add_argument("--preview", type=int, default=0, help="Preview N enriched metadata objects and exit (no index).")
    ap.add_argument("--skip-index", action="store_true", help="Write metadata but skip building the VectorStoreIndex (useful for metadata-only runs)")
    ap.add_argument("--llm-label", action="store_true", help="Call LLM to suggest ESMS labels for files (falls back to deterministic vocab matching if LLM not available)")
    ap.add_argument("--llm-overwrite", action="store_true", help="If set, overwrite title, description, and keywords in metadata with LLM suggestions.")
    ap.add_argument("--llm-vocab-only", action="store_true", help="When using LLM, restrict suggestions to the provided ESMS vocab candidates")
    ap.add_argument("--llm-temp", type=float, default=0.0, help="LLM temperature (default 0.0 for conservative suggestions)")
    ap.add_argument("--check-env", action="store_true", help="Check for optional reader libraries and exit")
    ap.add_argument("--max-bytes", type=int, default=MAX_BYTES, help=f"Size cap per file (default: {MAX_BYTES})")
    args = ap.parse_args()

    root = Path(args.root)
    persist_dir = Path(args.persist)

    # Fail early if the root doesn't exist to avoid silently creating an empty data folder
    if not root.exists():
        print(f"[ingest] Root folder does not exist: {root.resolve()}")
        print("Create the folder or pass --root to a folder that contains your data.")
        sys.exit(2)

    # Ensure persist directory exists (will be created if needed)
    persist_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(root, ALLOW_EXT, SKIP_EXT, args.max_bytes)
    # load ESMS vocab if requested
    vocab = {}
    if args.esms_vocab_dir:
        vocab = load_esms_vocab(Path(args.esms_vocab_dir))

    # Always use the six ESMS YAML templates in ./esms
    esms_template_dir = Path("./esms")
    esms_template_files = [
        esms_template_dir / "model_assessment.yaml",
        esms_template_dir / "model_identity_and_focus.yaml",
        esms_template_dir / "model_lifecycle_management.yaml",
        esms_template_dir / "model_representation.yaml",
        esms_template_dir / "model_scope_of_content.yaml",
        esms_template_dir / "model_utility.yaml",
    ]
    esms_templates = {}
    for tfile in esms_template_files:
        if tfile.exists():
            esms_templates[tfile.stem] = load_yaml_template(tfile)
        else:
            print(f"[esms] Template not found: {tfile}")

    def call_llm_for_labels(sample_md: Dict[str, Any], vocab_candidates: Dict[str, List[str]], temp: float, vocab_only: bool) -> Dict[str, Any]:
        """Attempt to call an LLM to suggest labels. On any error, fall back to a deterministic selection.

        Returns a dict suitable for inserting at md['esms']['llm_suggested']
        """
        # Build input for LLM
        # Prompt LLM to avoid generic answers and extract creative, content-specific metadata
        payload = {
            "title": sample_md.get("title"),
            "description": (sample_md.get("description") or "")[:1000],
            "sidecar": sample_md.get("sidecar") or {},
            "vocab_candidates": vocab_candidates or {},
            "instructions": (
                "You are a metadata assistant. For the given file, generate a creative, content-specific description and a list of highly relevant, non-trivial keywords/tags. "
                "Avoid generic answers like 'other', 'misc', or 'general'. Do not change the file's title or path. Return a JSON object with fields: description, keywords (list of strings), and any other useful metadata you can infer."
            )
        }

        # Try to call OpenAI-compatible API (best-effort). If not available, fallback.
        try:
            # Use new openai client pattern for LM Studio
            try:
                from openai import OpenAI
                client = OpenAI(
                    base_url=os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1"),
                    api_key=os.environ.get("OPENAI_API_KEY", "not-needed")
                )
                messages = [
                    {"role": "system", "content": "You are a metadata assistant. Return only JSON as specified."},
                    {"role": "user", "content": json.dumps(payload)}
                ]
                result_obj = client.chat.completions.create(
                    model=os.environ.get("OPENAI_MODEL", "openai/gpt-oss-20b"),
                    messages=messages,
                    temperature=temp,
                    max_tokens=512
                )
                text = result_obj.choices[0].message.content
                result = json.loads(text)
                return {"timestamp": __import__("datetime").datetime.utcnow().isoformat(), "model": getattr(result_obj, "model", None), "suggestions": result}
            except Exception:
                pass

            # Try llama-index Settings.llm if available
            try:
                from llama_index import StorageContext
                from llama_index.llms.openai import OpenAI as LlamaOpenAI
                llm = LlamaOpenAI(model=os.environ.get("LMSTUDIO_MODEL", "gpt-oss-20b"), temperature=temp)
                # llama-index OpenAI may not expose a direct chat API; try apredict or predict
                if hasattr(llm, "apredict"):
                    txt = llm.apredict(json.dumps(payload))
                elif hasattr(llm, "predict"):
                    txt = llm.predict(json.dumps(payload))
                else:
                    raise RuntimeError("llama-index OpenAI wrapper has no predict method")
                result = json.loads(txt)
                return {"timestamp": __import__("datetime").datetime.utcnow().isoformat(), "model": getattr(llm, "model", None), "suggestions": result}
            except Exception:
                pass
        except Exception:
            pass

        # Fallback: deterministic mapping from vocab_candidates -> choose top 1 per category if present
        suggestions = []
        for cat, terms in (vocab_candidates or {}).items():
            if not terms:
                continue
            # pick the longest term (heuristic) to avoid 'Other' being selected
            sel = max(terms, key=lambda t: (len(t), t))
            suggestions.append({"category": cat, "value": [sel], "rationale": "fallback deterministic pick from vocab"})
        return {"timestamp": __import__("datetime").datetime.utcnow().isoformat(), "model": "fallback", "suggestions": suggestions}

    if args.check_env:
        check_env()
        sys.exit(0)
    if args.dry_run:
        from collections import Counter
        c = Counter(p.suffix.lower() for p in files)
        print(f"[dry-run] Eligible files under {root.resolve()}: {len(files)}")
        for ext, n in sorted(c.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {ext or '<noext>'}: {n}")
        # show sample metadata if verbose
        if args.verbose and files:
            print("\n[dry-run] Sample metadata for first 3 files:")
            for fp in files[:3]:
                sidecar = load_sidecar(fp) if args.use_sidecar else None
                sample_text = read_text(fp, verbose=args.verbose)
                vm = match_esms_terms(sample_text + " " + fp.name, vocab, mode=args.esms_match_mode) if vocab else None
                meta = build_metadata(fp, sample_text, root, args, sidecar=sidecar, vocab_matches=vm)
                print(json.dumps(meta, indent=2)[:4000])
        sys.exit(0)

    if not files:
        print(f"[ingest] No eligible files found under {root.resolve()}.")
        sys.exit(0)

    print(f"[ingest] Found {len(files)} files. Reading & processing metadata…")
    docs: List[Document] = []
    skipped_empty = 0

    # Use tqdm if available for a progress bar
    try:
        from tqdm.auto import tqdm
        iterator = tqdm(files, desc="Reading files")
    except Exception:
        iterator = files

    meta_out_dir = Path(args.out_meta_dir)
    if not args.preview:
        meta_out_dir.mkdir(parents=True, exist_ok=True)
    combined_path = meta_out_dir / "metadata.jsonl"
    combined_f = combined_path.open("w", encoding="utf-8") if not args.preview else None


    saved_count = 0
    for fp in iterator:
        text = read_text(fp, verbose=args.verbose)
        if not text.strip():
            skipped_empty += 1
            continue
        sidecar = load_sidecar(fp) if args.use_sidecar else None
        vm = match_esms_terms(text + " " + fp.name, vocab, mode=args.esms_match_mode) if vocab else None
        md = build_metadata(fp, text, root, args, sidecar=sidecar, vocab_matches=vm)

        # --- New: For each ESMS template, fill out section using LLM ---
        esms_sections = {}
        if args.llm_label:
            for section, template in esms_templates.items():
                try:
                    # Limit file content and template size for prompt
                    short_content = text[:1500]
                    import yaml
                    short_template = yaml.safe_dump(template, sort_keys=False)
                    if len(short_template) > 1500:
                        short_template = short_template[:1500]
                    # Focused prompt for LLM
                    prompt = (
                        f"You are a metadata assistant. Given the following file content and a metadata template section, "
                        f"fill out as many fields as possible with specific, content-based information. "
                        f"If a field is not applicable, omit it, but keep the structure. "
                        f"Return only valid YAML for the section, with as many fields filled as possible.\n\n"
                        f"File content (truncated):\n{short_content}\n\n"
                        f"Template section (YAML, truncated):\n{short_template}\n"
                    )
                    from openai import OpenAI
                    client = OpenAI(
                        base_url=os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1"),
                        api_key=os.environ.get("OPENAI_API_KEY", "not-needed")
                    )
                    messages = [
                        {"role": "system", "content": "You are a metadata assistant. Return only YAML as specified."},
                        {"role": "user", "content": prompt}
                    ]
                    result_obj = client.chat.completions.create(
                        model=os.environ.get("OPENAI_MODEL", "openai/gpt-oss-20b"),
                        messages=messages,
                        temperature=args.llm_temp,
                        max_tokens=1024
                    )
                    text_out = result_obj.choices[0].message.content.strip()
                    # Log LLM response for debugging
                    if args.verbose:
                        print(f"[LLM][{section}] raw output:\n{text_out}\n---")
                    try:
                        section_data = yaml.safe_load(text_out)
                    except Exception as e_yaml:
                        if args.verbose:
                            print(f"[LLM][{section}] YAML parse error: {e_yaml}")
                        try:
                            section_data = json.loads(text_out)
                        except Exception as e_json:
                            if args.verbose:
                                print(f"[LLM][{section}] JSON parse error: {e_json}")
                            section_data = {}
                    esms_sections[section] = section_data
                except Exception as e:
                    if args.verbose:
                        print(f"[ingest] LLM ESMS section error for {fp} [{section}]: {e}")
                    esms_sections[section] = {}
        else:
            # fallback: just copy template structure, empty
            for section, template in esms_templates.items():
                esms_sections[section] = template

        md["esms_sections"] = esms_sections

        # preview handling
        if args.preview:
            print(json.dumps(md, indent=2)[:10000])
            saved_count += 1
            if saved_count >= args.preview:
                break
            continue

        # write per-file metadata YAML (fallback to json if yaml missing)
        out_fp = meta_out_dir / fp.relative_to(root)
        out_fp = out_fp.with_suffix(".yaml")
        out_fp.parent.mkdir(parents=True, exist_ok=True)
        try:
            import yaml
            out_fp.write_text(yaml.safe_dump(md, sort_keys=False), encoding="utf-8")
        except Exception:
            out_fp.write_text(json.dumps(md, indent=2), encoding="utf-8")

        # append to combined
        try:
            combined_f.write(json.dumps(md, ensure_ascii=False) + "\n")
        except Exception:
            pass

        docs.append(Document(text=text, metadata=md))

    if not docs:
        print("[ingest] No readable text extracted. (Files may be binary/CAD only.)")
        if args.verbose:
            print(f"[ingest] Skipped {skipped_empty} files that returned no text")
        sys.exit(0)

    index = VectorStoreIndex.from_documents(docs)
    index.storage_context.persist(persist_dir=str(persist_dir))
    print(f"[ingest] Indexed {len(docs)} docs; persisted to {persist_dir.resolve()}")

if __name__ == "__main__":
    main()
