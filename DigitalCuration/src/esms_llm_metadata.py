
"""esms_llm_metadata.py

Generate ESMS-formatted YAML metadata for each artifact by calling an LLM for each ESMS section.

Usage:
    python esms_llm_metadata.py --root ./data --esms-vocab-dir ./esms --preview 1

Environment:
    Requires LLM credentials (OPENAI/LMStudio) via environment variables.
"""

import os
from pathlib import Path
import yaml
import json
from openai import OpenAI
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **kwargs: x

def read_text(fp: Path) -> str:
    try:
        ext = fp.suffix.lower()
        if ext in {".txt", ".md", ".py", ".m", ".yaml", ".yml"}:
            return fp.read_text(encoding="utf-8", errors="ignore")
        if ext == ".csv":
            import pandas as pd
            df = pd.read_csv(fp, nrows=400)
            return df.to_csv(index=False)
        if ext == ".xlsx":
            import pandas as pd
            df = pd.read_excel(fp, nrows=200)
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
    return ""

def load_yaml_template(template_path: Path) -> dict:
    try:
        raw = template_path.read_text(encoding="utf-8", errors="ignore")
        return yaml.safe_load(raw)
    except Exception:
        return {}


def load_template_raw(template_path: Path) -> str:
    try:
        return template_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def load_esms_vocab(vocab_dir: Path) -> dict:
    out = {}
    if not vocab_dir.exists():
        return out
    for p in vocab_dir.iterdir():
        if not p.is_file() or p.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        key = p.stem.lower()
        # categorize by filename hints
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

        terms = []

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
        seen = set()
        uniq = []
        for t in terms:
            tl = t.lower()
            if tl in seen:
                continue
            seen.add(tl)
            uniq.append(t)
        out.setdefault(category, []).extend(uniq)
    return out


def match_esms_terms(sample: str, vocab: dict, mode: str = "heuristic") -> dict:
    matches = {}
    if not vocab:
        return matches
    s = (sample or "").lower()
    tokens = set(s.split())
    for cat, terms in vocab.items():
        for t in terms:
            tl = t.lower()
            if mode == "exact":
                if tl in tokens:
                    matches.setdefault(cat, []).append(t)
            else:
                if tl and tl in s:
                    matches.setdefault(cat, []).append(t)
    return matches

def llm_fill_section(section_name, template_raw, file_content, model, client, temp=0.0):
    # template_raw: the raw YAML template text (string)
    short_content = (file_content or "")[:1600]
    short_template = (template_raw or "")[:1600]
    prompt = (
        "You are a metadata assistant. You will be given: (1) a truncated file content, and (2) the exact YAML template for a single ESMS section.\n"
        "Your job: return a YAML object that follows the same structure as the template and fills in as many fields as possible with specific, content-derived values.\n"
        "Rules:\n"
        "- Do NOT add or remove top-level ESMS section names; only fill inside the provided section structure.\n"
        "- Prefer to select from the explicit keys/choices in the template. If none of the listed choices apply, DO NOT return the literal string 'Other' or 'Misc'. Instead, provide a concise, specific value that accurately describes the file (e.g., 'Custom: <your value>').\n"
        "- If the template lists multiple allowed choices, return the subset that best applies.\n"
        "- If a field is not applicable, omit it rather than populating with 'N/A'.\n"
        "- Return only valid YAML for the section (no surrounding prose).\n\n"
        f"File content (truncated):\n{short_content}\n\n"
        f"Template section (exact YAML, truncated):\n{short_template}\n\n"
        f"Now produce the YAML for the section '{section_name}'."
    )
    messages = [
        {"role": "system", "content": "You are a metadata assistant. Return only YAML that conforms to the provided template structure."},
        {"role": "user", "content": prompt}
    ]
    result_obj = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temp,
        max_tokens=1200
    )
    text_out = (result_obj.choices[0].message.content or "").strip()
    # Try parse as YAML, then JSON, otherwise fallback to empty dict
    try:
        parsed = yaml.safe_load(text_out)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    try:
        parsed = json.loads(text_out)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    # if parsing failed, return empty dict to keep schema intact
    return {}

def main():
    data_dir = Path("./data")
    esms_dir = Path("./esms")
    out_dir = Path("./metadata")
    out_dir.mkdir(parents=True, exist_ok=True)

    model = os.environ.get("OPENAI_MODEL", "openai/gpt-oss-20b")
    client = OpenAI(
        base_url=os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1"),
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed")
    )

    # canonical required sections mapped to template filenames
    template_files = {
        "assessment": esms_dir / "model_assessment.yaml",
        "identity_and_focus": esms_dir / "model_identity_and_focus.yaml",
        "lifecycle_management": esms_dir / "model_lifecycle_management.yaml",
        "representation": esms_dir / "model_representation.yaml",
        "scope_of_content": esms_dir / "model_scope_of_content.yaml",
        "utility": esms_dir / "model_utility.yaml",
    }

    # load parsed and raw templates
    esms_templates = {}
    for key, path in template_files.items():
        if path.exists():
            esms_templates[key] = {"parsed": load_yaml_template(path), "raw": load_template_raw(path)}
        else:
            esms_templates[key] = {"parsed": {}, "raw": ""}

    files = [fp for fp in data_dir.rglob("*") if fp.is_file()]
    for fp in tqdm(files, desc="Processing files"):
        try:
            rel_path = str(fp.relative_to(Path(".")))
        except Exception:
            rel_path = str(fp)

        file_content = read_text(fp)
        if not file_content.strip():
            print(f"[INFO] Skipping (no readable text): {fp}")
            continue

        metadata = {"file_name": fp.name, "file_path": str(fp.resolve()), "rel_path": rel_path, "title": fp.stem}

        # Always call LLM for each of the six required sections, using raw template text as guidance
        for section in ["identity_and_focus", "scope_of_content", "representation", "utility", "assessment", "lifecycle_management"]:
            template_raw = esms_templates.get(section, {}).get("raw", "")
            print(f"[INFO] Processing file: {fp} -> section: {section}")
            try:
                parsed = llm_fill_section(section, template_raw, file_content, model, client)
                metadata[section] = parsed if isinstance(parsed, dict) else {}
            except Exception as e:
                print(f"[ERROR] LLM failed for {fp} [{section}]: {e}")
                metadata[section] = {}

        out_fp = out_dir / Path(rel_path).with_suffix(".yaml")
        out_fp.parent.mkdir(parents=True, exist_ok=True)
        out_obj = {"file_name": metadata["file_name"], "file_path": metadata["file_path"], "rel_path": metadata["rel_path"], "title": metadata.get("title", "")}
        for section in ["identity_and_focus", "scope_of_content", "representation", "utility", "assessment", "lifecycle_management"]:
            out_obj[section] = metadata.get(section, {})

        with out_fp.open("w", encoding="utf-8") as f:
            yaml.safe_dump(out_obj, f, sort_keys=False)
        print(f"Wrote: {out_fp}")

if __name__ == "__main__":
    main()
