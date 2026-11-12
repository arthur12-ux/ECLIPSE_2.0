"""apply_esms_with_lmstudio.py

Wrapper to apply ESMS templates using an LLM endpoint (LM Studio / OpenAI-compatible).

Usage:
    python apply_esms_with_lmstudio.py [--root ./data] [--esms-vocab-dir ./esms]

Environment:
    Set LLM credentials via environment variables (e.g. OPENAI_API_BASE, OPENAI_API_KEY).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union
import argparse, json, os, requests

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

# ---------- YAML setup ----------
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=2, offset=2)

ROOT_SECTIONS = [
    "identity_and_focus",
    "scope_of_content",
    "representation",
    "utility",
    "assessment",
    "lifecycle_management",
]

# Allowed ESMS paths (ONLY these will be written)
ALLOWED_PATHS = set([
    # identity_and_focus
    "identity_and_focus.es_model_identity",
    "identity_and_focus.es_model_purpose",
    "identity_and_focus.system_of_interest",
    "identity_and_focus.modeled_domains",
    "identity_and_focus.modeled_scenarios",
    "identity_and_focus.stakeholders",
    "identity_and_focus.originating_org",
    "identity_and_focus.related_program",
    "identity_and_focus.keywords",

    # scope_of_content
    "scope_of_content.stakeholder_values_of_interest",
    "scope_of_content.external_interactions",
    "scope_of_content.internal_interactions",
    "scope_of_content.model_components",
    "scope_of_content.datasets",

    # representation (conceptual)
    "representation.conceptual.simulation_methods",
    "representation.conceptual.analysis_methods",
    "representation.conceptual.physical_domains",
    "representation.conceptual.data_relationships",
    "representation.conceptual.time_fidelity",
    "representation.conceptual.behavior_fidelity",

    # representation (executable)
    "representation.executable.model_type",
    "representation.executable.modeling_language",
    "representation.executable.submodels_used",

    # utility
    "utility.lifecycle_processes_supported",
    "utility.application_envelope",
    "utility.parametric_support",
    "utility.simulation_phase",
    "utility.perceived_complexity",
    "utility.intended_use",

    # assessment (keep high-level, sparse)
    "assessment.qualification_summary",
    "assessment.evaluation_scope",
    "assessment.code_verification.methods",
    "assessment.solution_verification.methods",
    "assessment.validation.methods",
    "assessment.uq_sensitivity.methods",
    "assessment.appropriateness.frameworks",
    "assessment.standards_compliance",

    # lifecycle_management
    "lifecycle_management.version",
    "lifecycle_management.config",
    "lifecycle_management.it_requirements",
    "lifecycle_management.maintenance_method",
    "lifecycle_management.deployment_method",
    "lifecycle_management.governing_body",
    "lifecycle_management.version_status",
    "lifecycle_management.date_created",
    "lifecycle_management.last_modified",
])

# ---------- Helpers ----------
def is_empty(x: Any) -> bool:
    if x is None: return True
    if isinstance(x, str): return x.strip() == ""
    if isinstance(x, (list, tuple, set)): return all(is_empty(v) for v in x)
    if isinstance(x, dict): return all(is_empty(v) for v in x.values())
    return False

def prune_empty(obj: Any) -> Any:
    if isinstance(obj, CommentedMap):
        for k in list(obj.keys()):
            obj[k] = prune_empty(obj[k])
            if is_empty(obj[k]):
                del obj[k]
        return obj
    elif isinstance(obj, CommentedSeq):
        for i in range(len(obj)):
            obj[i] = prune_empty(obj[i])
        kept = [v for v in obj if not is_empty(v)]
        obj.clear(); obj.extend(kept)
        return obj
    return obj

def ensure_root_sections(doc: CommentedMap):
    for sec in ROOT_SECTIONS:
        if sec not in doc or not isinstance(doc.get(sec), CommentedMap):
            doc[sec] = CommentedMap()

def compact_empty_sections(doc: CommentedMap):
    for sec in ROOT_SECTIONS:
        if sec in doc and isinstance(doc[sec], dict) and not len(doc[sec]):
            doc[sec] = CommentedMap()  # renders as {}

def ensure_path(root: CommentedMap, path: str) -> Tuple[CommentedMap|CommentedSeq, str]:
    parts = path.split(".")
    parent: Union[CommentedMap, CommentedSeq] = root
    for p in parts[:-1]:
        if isinstance(parent, CommentedMap):
            if p not in parent or not isinstance(parent[p], CommentedMap):
                parent[p] = CommentedMap()
            parent = parent[p]
        else:
            raise KeyError(f"Cannot descend into non-map at {p}")
    return parent, parts[-1]

def hoist_and_strip(doc: CommentedMap):
    # If fields are under esms, hoist 6 sections, drop vocab_matches & llm_suggested leftovers.
    if "esms" in doc and isinstance(doc["esms"], CommentedMap):
        es = doc["esms"]
        # remove vocab_matches
        if "vocab_matches" in es:
            del es["vocab_matches"]
        # move sections up
        for sec in ROOT_SECTIONS:
            if sec in es:
                doc[sec] = es.pop(sec)
        # hoist llm_suggested so we can consume it
        if "llm_suggested" in es:
            doc["llm_suggested"] = es.pop("llm_suggested")
        if not len(es):
            del doc["esms"]
    # also strip any top-level vocab_matches
    if "vocab_matches" in doc:
        del doc["vocab_matches"]

def get_llm_suggestions(doc: CommentedMap) -> List[Dict[str, Any]]:
    # Accept either:
    #   llm_suggested: { suggestions: [...] }  OR
    #   llm_suggested: [ {path,value} , ... ] OR nested by category
    sugg = doc.get("llm_suggested")
    if sugg is None and "esms" in doc and isinstance(doc["esms"], CommentedMap):
        sugg = doc["esms"].get("llm_suggested")
    if sugg is None:
        return []
    if isinstance(sugg, dict) and "suggestions" in sugg and isinstance(sugg["suggestions"], list):
        return sugg["suggestions"]
    if isinstance(sugg, list):
        return sugg
    # nested dict by categories -> flatten
    if isinstance(sugg, dict):
        out = []
        for cat, body in sugg.items():
            if not isinstance(body, dict): continue
            for k, v in body.items():
                out.append({"category": cat, "field": k, "value": v})
        return out
    return []

# ---------- LM Studio ----------
SYSTEM_PRIMER = """You are an ESMS metadata assistant. You will map each suggestion to exactly one of the allowed ESMS fields. 
Return ONLY valid JSON with keys: path (string), value (string|array). 
Never invent fields; you must choose from the allowed list."""

def choose_field_via_llm(base_url: str, api_key: str, model: str, hint: Dict[str, Any], allowed_paths: List[str]) -> Tuple[str, Any] | None:
    """
    Ask LM Studio to choose the best allowed path for this suggestion.
    hint can contain: category, field, value, description, mime_type, title, filename
    Returns (path, value) or None on failure.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    user = {
        "hint": hint,
        "allowed_paths": allowed_paths
    }
    payload = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM_PRIMER},
            {"role": "user", "content": json.dumps(user)}
        ]
    }
    try:
        r = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        data = json.loads(content)
        path = data.get("path")
        val = data.get("value")
        if isinstance(path, str) and path in ALLOWED_PATHS:
            return path, val
    except Exception:
        return None
    return None

# ---------- MIME inference ----------
def mime_infer(doc: CommentedMap):
    mt = doc.get("mime_type", "")
    if not isinstance(mt, str):
        return
    ensure_root_sections(doc)
    rep = doc["representation"]
    if "executable" not in rep: rep["executable"] = CommentedMap()
    if "conceptual" not in rep: rep["conceptual"] = CommentedMap()
    if "spreadsheetml.sheet" in mt:
        rep["executable"]["model_type"] = rep["executable"].get("model_type") or "spreadsheet"
        rep["executable"]["modeling_language"] = rep["executable"].get("modeling_language") or "Excel/OpenXML"
        lm = doc["lifecycle_management"]
        if "it_requirements" not in lm or is_empty(lm.get("it_requirements")):
            lm["it_requirements"] = ["Microsoft Excel"]
    elif "wordprocessingml.document" in mt:
        rep["executable"]["model_type"] = rep["executable"].get("model_type") or "document"
        rep["executable"]["modeling_language"] = rep["executable"].get("modeling_language") or "Word/OpenXML"
        lm = doc["lifecycle_management"]
        if "it_requirements" not in lm or is_empty(lm.get("it_requirements")):
            lm["it_requirements"] = ["Microsoft Word"]
    elif mt == "application/pdf":
        rep["executable"]["model_type"] = rep["executable"].get("model_type") or "document"
        rep["executable"]["modeling_language"] = rep["executable"].get("modeling_language") or "PDF"

# ---------- Processing ----------
def apply_mapping(doc: CommentedMap, path: str, value: Any, force: bool) -> bool:
    """Write value at path if allowed & empty (or --force). Returns True if applied."""
    if path not in ALLOWED_PATHS:
        return False
    parent, key = ensure_path(doc, path)
    current = parent.get(key)
    if (not force) and (current not in (None, "", [], {})):
        # allow list replacement of "other"/null slots
        if isinstance(current, list) and isinstance(value, list):
            changed = False
            merged = list(current)
            j = 0
            for i, item in enumerate(merged):
                if item is None or (isinstance(item, str) and item.strip().lower() == "other"):
                    if j < len(value):
                        merged[i] = value[j]; j += 1; changed = True
            if changed:
                parent[key] = merged
                return True
        return False
    parent[key] = value
    return True

def process_yaml(fp: Path, base_url: str, api_key: str, model: str, force: bool, backup: bool) -> Tuple[int,int]:
    try:
        data = yaml.load(fp.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[skip] {fp} (parse error: {e})"); return (0,0)
    if not isinstance(data, CommentedMap):
        return (0,0)

    hoist_and_strip(data)
    ensure_root_sections(data)

    # Prepare context hints
    ctx = {
        "title": data.get("title"),
        "filename": data.get("file_name"),
        "mime_type": data.get("mime_type"),
        "description": data.get("description"),
    }

    suggestions = get_llm_suggestions(data)
    applied = skipped = 0

    for s in suggestions:
        # Normalize hint
        hint = {
            "category": s.get("category") or s.get("cat"),
            "field": s.get("field"),
            "value": s.get("value"),
            "description": ctx["description"],
            "mime_type": ctx["mime_type"],
            "title": ctx["title"],
            "filename": ctx["filename"],
        }
        # If a dot-path is given explicitly, prefer it (if allowed).
        explicit_path = s.get("path")
        if isinstance(explicit_path, str) and explicit_path in ALLOWED_PATHS:
            ok = apply_mapping(data, explicit_path, s.get("value"), force)
            applied += int(ok); skipped += int(not ok)
            continue

        # Ask LM Studio to select the path from ALLOWED_PATHS
        choice = choose_field_via_llm(base_url, api_key, model, hint, sorted(list(ALLOWED_PATHS)))
        if not choice:
            skipped += 1
            continue
        path, val = choice
        ok = apply_mapping(data, path, val, force)
        applied += int(ok); skipped += int(not ok)

    # Remove llm_suggested everywhere
    if "llm_suggested" in data: del data["llm_suggested"]
    if "esms" in data and isinstance(data["esms"], CommentedMap) and "llm_suggested" in data["esms"]:
        del data["esms"]["llm_suggested"]

    # Lightweight MIME-based fill-ins
    mime_infer(data)

    # Sparse output
    data = prune_empty(data)
    # Keep six sections at root even if empty
    for sec in ROOT_SECTIONS:
        if sec not in data:
            data[sec] = CommentedMap()
    compact_empty_sections(data)

    # Write back
    if not backup:
        fp.write_text("")  # reduce partial overwrite risk
    if backup:
        bak = fp.with_suffix(fp.suffix + ".bak")
        if not bak.exists():
            bak.write_text(fp.read_text(encoding="utf-8"), encoding="utf-8")
    with fp.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    return applied, skipped

def main():
    p = argparse.ArgumentParser(description="Apply ESMS suggestions using LM Studio (recursive).")
    p.add_argument("--folder", required=True, help="Root folder to scan")
    p.add_argument("--model", default=os.environ.get("LMSTUDIO_MODEL", "gpt-oss-20b"))
    p.add_argument("--force", action="store_true", help="Overwrite non-empty fields")
    p.add_argument("--no-backup", action="store_true", help="Do not create .bak backups")
    p.add_argument("--exts", default="yaml,yml", help="Comma-separated extensions")
    args = p.parse_args()

    base_url = os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1")
    api_key  = os.environ.get("OPENAI_API_KEY", "not-needed")
    exts = tuple("." + e.strip().lower() for e in args.exts.split(",") if e.strip())

    total_files = total_applied = total_skipped = 0
    for fp in Path(args.folder).rglob("*"):
        if not (fp.is_file() and fp.suffix.lower() in exts):
            continue
        total_files += 1
        a, s = process_yaml(fp, base_url, api_key, args.model, force=args.force, backup=not args.no_backup)
        total_applied += a; total_skipped += s
        if a or s:
            print(f"[{fp}] applied:{a} skipped:{s}")
    print(f"SUMMARY → files:{total_files} applied:{total_applied} skipped:{total_skipped}")

if __name__ == "__main__":
    main()
