# apply_llm_suggestions.py
# Recursively apply values from `llm_suggested` into ESMS YAML fields, then remove `llm_suggested`.
# Preserves formatting/comments via ruamel.yaml.

"""apply_llm_suggestions.py

Apply suggested edits from an LLM to existing metadata files.

Usage:
    python apply_llm_suggestions.py --metadata-dir ./metadata

Environment:
    Requires LLM credentials in environment variables (OPENAI_API_KEY or LMSTUDIO keys).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Tuple, Union
import argparse
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=2, offset=2)

ESMS_CATS = {
    "identity_and_focus",
    "scope_of_content",
    "representation",
    "utility",
    "assessment",
    "lifecycle_management",
}

def is_other_or_null(v: Any) -> bool:
    if v is None:
        return True
    return isinstance(v, str) and v.strip().lower() == "other"

def get_node_by_path(root: Union[CommentedMap, CommentedSeq], path: str) -> Tuple[Union[CommentedMap, CommentedSeq], str]:
    parts = path.split(".")
    parent = root
    for p in parts[:-1]:
        if not isinstance(parent, CommentedMap) or p not in parent:
            raise KeyError(f"missing path component: {p}")
        parent = parent[p]
    return parent, parts[-1]

def set_value(parent: Union[CommentedMap, CommentedSeq], key: str, value: Any, add_comment: bool = True):
    parent[key] = value
    if isinstance(parent, CommentedMap) and add_comment:
        parent.yaml_set_comment_before_after_key(key, after=" LLM-suggested")

def iter_dotpath_suggestions(sugg: Iterable[dict]) -> Iterable[Tuple[str, Any]]:
    for item in sugg:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        val = item.get("value")
        if isinstance(path, str):
            yield path, val

def iter_nested_suggestions(sugg_root: dict) -> Iterable[Tuple[str, Any]]:
    for cat, items in sugg_root.items():
        if cat not in ESMS_CATS or not isinstance(items, dict):
            continue
        for k, v in items.items():
            if isinstance(k, str) and "." in k:
                yield f"{cat}.{k}", v
            else:
                yield f"{cat}.{k}", v

def apply_suggestions(doc: CommentedMap, force: bool = False) -> Tuple[int, int]:
    if "llm_suggested" not in doc:
        return (0, 0)

    sugg = doc["llm_suggested"]
    applied = 0
    skipped = 0

    if isinstance(sugg, list):
        pairs = iter_dotpath_suggestions(sugg)
    elif isinstance(sugg, dict):
        pairs = iter_nested_suggestions(sugg)
    else:
        return (0, 0)

    for path, val in pairs:
        try:
            parent, key = get_node_by_path(doc, path)
        except KeyError:
            skipped += 1
            continue

        try:
            current = parent[key]
        except Exception:
            parent[key] = val
            applied += 1
            continue

        if force or is_other_or_null(current):
            set_value(parent, key, val, add_comment=True)
            applied += 1
        else:
            if isinstance(current, list) and isinstance(val, list):
                merged = list(current)
                j = 0
                changed = False
                for i, item in enumerate(merged):
                    if is_other_or_null(item) and j < len(val):
                        merged[i] = val[j]
                        j += 1
                        changed = True
                if changed:
                    set_value(parent, key, merged, add_comment=True)
                    applied += 1
                else:
                    skipped += 1
            else:
                skipped += 1

    try:
        del doc["llm_suggested"]
    except Exception:
        pass

    return applied, skipped

def process_file(in_path: Path, force: bool = False, backup: bool = True) -> Tuple[int, int]:
    try:
        data = yaml.load(in_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[skip] {in_path} (YAML parse error: {e})")
        return (0, 0)

    if not isinstance(data, CommentedMap):
        print(f"[skip] {in_path} (root is not a mapping)")
        return (0, 0)

    applied, skipped = apply_suggestions(data, force=force)

    if applied > 0:
        if not backup:
            in_path.write_text("")  # ensure we don't partially overwrite on error
        if backup:
            bak = in_path.with_suffix(in_path.suffix + ".bak")
            if not bak.exists():
                bak.write_text(in_path.read_text(encoding="utf-8"), encoding="utf-8")
        with in_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)

    return applied, skipped

def main():
    ap = argparse.ArgumentParser(description="Recursively apply llm_suggested values into ESMS YAML files.")
    ap.add_argument("--folder", required=True, help="Root folder to scan (recursively)")
    ap.add_argument("--force", action="store_true", help="Replace even when field has a non-'other' value")
    ap.add_argument("--no-backup", action="store_true", help="Do not create .bak backups when writing")
    ap.add_argument("--exts", default="yaml,yml", help="Comma-separated extensions to include (default: yaml,yml)")
    args = ap.parse_args()

    root = Path(args.folder)
    if not root.exists():
        print(f"[error] folder not found: {root}")
        return

    exts = tuple("." + e.strip().lower() for e in args.exts.split(",") if e.strip())
    total_files = total_applied = total_skipped = 0

    for fp in root.rglob("*"):
        if not fp.is_file():
            continue
        if fp.suffix.lower() not in exts:
            continue
        total_files += 1
        applied, skipped = process_file(fp, force=args.force, backup=not args.no_backup)
        if applied or skipped:
            print(f"[{fp}] applied: {applied}, skipped: {skipped}")
        total_applied += applied
        total_skipped += skipped

    print(f"SUMMARY → files scanned: {total_files}, applied: {total_applied}, skipped: {total_skipped}")

if __name__ == "__main__":
    main()
