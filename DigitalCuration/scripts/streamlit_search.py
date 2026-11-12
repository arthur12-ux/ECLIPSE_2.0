"""scripts/streamlit_search.py

Streamlit UI for searching the persisted semantic index. Presents a sidebar
search box and displays matching documents with paths and scores.

Run:
    python -m streamlit run scripts/streamlit_search.py --server.port 8501
"""

import os
import json
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer

import streamlit as st
import yaml
from urllib.parse import quote
import html as _html

PERSIST_DIR = Path("./storage")
META_PATH = PERSIST_DIR / "meta.json"
NBRS_PATH = PERSIST_DIR / "nbrs.pkl"
EMB_PATH = PERSIST_DIR / "embeddings.npy"

# Port for the optional local static server helper (see scripts/serve_data.py)
STATIC_SERVER_PORT = 8502

def _open_local(path, reveal=False):
    """Open a file with the OS default application (or reveal it in the file browser)."""
    import subprocess
    import sys
    p = str(Path(path).resolve())
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-R", p] if reveal else ["open", p])
    elif sys.platform.startswith("win"):
        if reveal:
            subprocess.Popen(["explorer", "/select,", p])
        else:
            os.startfile(p)
    else:
        subprocess.Popen(["xdg-open", str(Path(p).parent) if reveal else p])


@st.cache_resource
def load_model(name="all-MiniLM-L6-v2"):
    return SentenceTransformer(name)

@st.cache_data
def load_meta():
    if not META_PATH.exists():
        return None
    return json.loads(META_PATH.read_text(encoding='utf-8'))

@st.cache_data
def load_nbrs():
    if not NBRS_PATH.exists():
        return None
    with open(NBRS_PATH, 'rb') as f:
        return pickle.load(f)

st.set_page_config(page_title="Digital Curation Search", layout="wide")
st.title("ASDL Digital Curator")

meta = load_meta()
nbrs = load_nbrs()

if meta is None or nbrs is None:
    st.error("Persisted index artifacts not found in ./storage. Run the index builder (`index_and_query.py`) first.")
    st.stop()

model = load_model()

# Sidebar
with st.sidebar:
    st.header("Search options")
    # Use a fixed Top K default of 10 (no slider in UI)
    top_k = 10
    # Move the primary search input into the sidebar (replaces the previous sample query UI)
    query = st.text_input("Search query", "lunar habitat")
    # Optionally return all indexed documents (may be many and slow to render)
    show_all = st.checkbox("Show all indexed results", value=False, help="When checked, return every indexed document (may be slow in the browser)")
    # File type filter: collect extensions from the raw sources referenced by the index metadata
    def _resolve_raw_ext(meta_item):
        try:
            src = Path(meta_item.get('source', ''))
            # If the meta source is a YAML, try to find the original file inside it
            if src.suffix.lower() in ('.yaml', '.yml') and src.exists():
                try:
                    raw = yaml.safe_load(src.read_text(encoding='utf-8', errors='ignore')) or {}
                except Exception:
                    raw = {}
                for k in ('file_path', 'original_path', 'original_file', 'source', 'file_name', 'path', 'location'):
                    v = raw.get(k)
                    if v:
                        p = Path(v)
                        if p.suffix:
                            return p.suffix.lower()
                        # try to find by filename under data/
                        matches = list(Path('./data').rglob(str(Path(v).name)))
                        if matches:
                            return matches[0].suffix.lower()
                # fallback: search for files in data with same stem as the yaml filename
                stem = src.stem
                matches = list(Path('./data').rglob(f"{stem}.*"))
                if matches:
                    return matches[0].suffix.lower()
                return ''
            else:
                return src.suffix.lower()
        except Exception:
            return ''

    def _resolve_raw_path(meta_item):
        """Return a Path to the raw source file when available, otherwise None.

        This mirrors the extension-resolution logic but returns the actual Path
        so the UI can link to the real file instead of the YAML metadata file.
        """
        try:
            src = Path(meta_item.get('source', ''))
            if src.suffix.lower() in ('.yaml', '.yml') and src.exists():
                try:
                    raw = yaml.safe_load(src.read_text(encoding='utf-8', errors='ignore')) or {}
                except Exception:
                    raw = {}
                # Look for explicit original file references
                for k in ('file_path', 'original_path', 'original_file', 'source', 'file_name', 'path', 'location'):
                    v = raw.get(k)
                    if v:
                        p = Path(v)
                        if p.is_absolute() and p.exists():
                            return p
                        # try to find by filename under data/
                        matches = list(Path('./data').rglob(str(Path(v).name)))
                        if matches:
                            return matches[0]
                # fallback: search for files in data with same stem as the yaml filename
                stem = src.stem
                matches = list(Path('./data').rglob(f"{stem}.*"))
                if matches:
                    return matches[0]
                return None
            else:
                # If the source is not a YAML, return it if it exists (or return it anyway)
                if src.exists():
                    return src
                return src
        except Exception:
            return None

    try:
        exts = sorted({_resolve_raw_ext(item) for item in (meta or []) if _resolve_raw_ext(item)})
    except Exception:
        exts = []

    # Map extensions to color emojis for display in the dropdown
    emoji_map = {
        '.pdf': '🟥', '.yaml': '🟦', '.yml': '🟦', '.txt': '🟩', '.m': '🟪',
        '.docx': '🟧', '.csv': '🟩', '.xlsx': '🟦', '.sldprt': '🔶', '.sldasm': '🔶',
        '.step': '🟣', '.stp': '🟣', '.iges': '🔷', '.igs': '🔷', '.stl': '🟢',
        '.obj': '🔵', '.prt': '🟩', '.ipt': '🟤', '.iam': '🟥', '.f3d': '🟠',
        '.sat': '🔵', '.x_t': '🟨', '.x_b': '🟨', '.3mf': '🟪', '.dwg': '⬛', '.dxf': '⬛',
        '.ply': '🟫'
    }

    # Build option labels that include a colored emoji followed by the extension
    option_labels = ["All"] + [f"{emoji_map.get(e, '⚪')} {e}" for e in exts]
    # Show the multiselect with colored emoji prefixes. We'll map selected labels back to extensions.
    selected_labels = st.multiselect("Filter by file type", options=option_labels, default=["All"], help="Select one or more file extensions to restrict search results")
    # Map selected labels back to extension strings (e.g., '🟥 .pdf' -> '.pdf')
    selected_types = []
    if selected_labels:
        for lab in selected_labels:
            if lab == "All":
                selected_types = ["All"]
                break
            # label format: '{emoji} {ext}'
            parts = lab.split() if isinstance(lab, str) else [lab]
            if parts:
                selected_types.append(parts[-1])

    # Color mapping for file extensions (customize as needed)
    ext_color_map = {
        '.pdf': '#d9534f',
        '.yaml': '#0275d8',
        '.yml': '#0275d8',
        '.txt': '#5cb85c',
        '.m': '#6f42c1',
        '.docx': '#f0ad4e',
        '.csv': '#20c997',
        '.xlsx': '#17a2b8',
        # Common CAD and engineering formats
        '.sldprt': '#ff7f50',   # SolidWorks part
        '.sldasm': '#ff6347',   # SolidWorks assembly
        '.step': '#8a2be2',     # STEP
        '.stp': '#8a2be2',      # STEP alternate
        '.iges': '#ff69b4',     # IGES
        '.igs': '#ff69b4',      # IGES alternate
        '.stl': '#2e8b57',      # STL (meshes)
        '.obj': '#1e90ff',      # OBJ (meshes)
        '.prt': '#20b2aa',      # Generic part file
        '.ipt': '#a0522d',      # Inventor part
        '.iam': '#cd5c5c',      # Inventor assembly
        '.f3d': '#ff8c00',      # Fusion 360
        '.sat': '#4682b4',      # ACIS SAT
        '.x_t': '#9acd32',      # Parasolid text
        '.x_b': '#9acd32',      # Parasolid binary
        '.3mf': '#6a5acd',      # 3MF
        '.dwg': '#2f4f4f',      # AutoCAD drawing
        '.dxf': '#708090',      # AutoCAD exchange
        '.ply': '#b8860b'       # PLY mesh
    }

    def color_for_ext(ext: str) -> str:
        if not ext:
            return '#6c757d'  # gray for unknown
        return ext_color_map.get(ext.lower(), '#6c757d')

    # Score range slider: allow users to filter results by score (0.0 - 1.0)
    score_range = st.slider("Score range", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.01, help="Filter results to only show items with scores inside this range")
    score_min, score_max = float(score_range[0]), float(score_range[1])

if not query:
    st.info("Type a query in the sidebar search box and press Enter.")
else:
    # If the user asked to show all results, warn about rendering many items
    try:
        total_indexed = len(meta) if isinstance(meta, list) else None
    except Exception:
        total_indexed = None

    if 'show_all' in locals() and show_all and total_indexed is not None:
        st.info(f"Show all enabled: returning {total_indexed} results — this may be slow to render in the browser.")

    with st.spinner("Encoding query and searching..."):
        q_emb = model.encode([query])
        try:
            # Clamp requested neighbors to the number of indexed documents to avoid errors
            max_available = len(meta) if isinstance(meta, list) else 0
            # Request distances to all indexed items so we can apply extension filters locally
            n_neighbors = max_available if max_available > 0 else top_k
            dists, idxs = nbrs.kneighbors(q_emb, n_neighbors=n_neighbors)
        except Exception as e:
            st.error(f"Search failed: {e}")
            st.stop()

        # Build ordered list of (dist, idx) and apply file-type filtering
        ordered = list(zip(dists[0], idxs[0]))
        # Determine allowed extensions: if "All" selected or nothing selected, allow all
        allow_all = (not selected_types) or ("All" in selected_types)
        allowed_exts = {t.lower() for t in selected_types if t != "All"}

        results = []
        for dist, idx in ordered:
            meta_item = meta[idx]
            src = Path(meta_item.get('source', ''))
            # Try to resolve the raw source file (prefer raw files over YAML metadata)
            raw_path = _resolve_raw_path(meta_item)
            raw_ext = (raw_path.suffix.lower() if raw_path and getattr(raw_path, 'suffix', None) else src.suffix.lower())
            # If filtering by type, skip items that don't match (compare against resolved raw extension)
            if not allow_all:
                if raw_ext not in allowed_exts:
                    continue
            score = 1 - float(dist)
            # Filter by score range selected in the sidebar
            if score < score_min or score > score_max:
                continue
            snippet = ''
            parsed_meta = {}

            # If the source is a YAML metadata file, try to parse common fields
            try:
                if src.suffix.lower() in ('.yaml', '.yml') and src.exists():
                    raw = yaml.safe_load(src.read_text(encoding='utf-8', errors='ignore'))
                    # Look for common keys used in ESMS templates
                    for key in ('model_title', 'title', 'model_identifier', 'file_name'):
                        if key in raw:
                            parsed_meta[key] = raw.get(key)
                    # Sometimes nested under model_identity_and_focus
                    mid = raw.get('model_identity_and_focus') or raw.get('identity_and_focus')
                    if isinstance(mid, dict):
                        for key in ('model_title', 'model_identifier', 'model_developer'):
                            if key in mid:
                                parsed_meta.setdefault(key, mid.get(key))
            except Exception:
                parsed_meta = {}

            # Prefer storing the raw source in the result so the UI links to the actual file
            display_source = raw_path if raw_path is not None else src
            # Keep track of the YAML metadata path when present so the UI can link to it
            yaml_source = str(src) if src.suffix.lower() in ('.yaml', '.yml') else None
            results.append({'score': score, 'source': str(display_source), 'raw_source': str(raw_path) if raw_path is not None else None, 'yaml_source': yaml_source, 'snippet': snippet, 'meta': parsed_meta})
        # If not showing all results, limit to top_k after filtering
        if not (('show_all' in locals() and show_all)):
            results = results[:top_k]

    st.subheader(f"Results for: '{query}'")
    for r in results:
        # Determine display name: prefer parsed title/model_title or filename
        parsed = r.get('meta') or {}
        display_name = parsed.get('model_title') or parsed.get('title') or parsed.get('file_name') or Path(r['source']).name

        # Compute extension color and label (include emoji if available)
        src_path = Path(r['source'])
        ext = src_path.suffix.lower()
        badge_color = color_for_ext(ext)
        emoji = emoji_map.get(ext, '⚪')
        badge_label = f"{emoji} {ext if ext else 'other'}"

        # Layout: small badge column + expander column
        col_badge, col_exp = st.columns([0.06, 0.94])
        with col_badge:
            # Render a small colored badge for the file type
            badge_html = f"<div style='display:inline-block;padding:6px 8px;background:{badge_color};color:white;border-radius:6px;font-size:12px;text-align:center'>{badge_label}</div>"
            st.markdown(badge_html, unsafe_allow_html=True)

        # Expander label shows the actual name
        exp = col_exp.expander(f"{display_name}")
        with exp:
            # Inside the dropdown show score and path (no snippet)
            st.markdown(f"**Score:** {r['score']:.3f}")

            # Resolve display path earlier and render it immediately after the score
            display_path = Path(r['source'])
            fm = parsed
            candidate = None
            for k in ('file_path', 'file_name', 'original_path', 'original_file', 'source'):
                if k in fm and fm.get(k):
                    candidate = fm.get(k)
                    break
            if candidate:
                try:
                    cand_path = Path(candidate)
                    if cand_path.is_absolute() and cand_path.exists():
                        display_path = cand_path
                    else:
                        possible = list(Path('./data').rglob(str(cand_path.name)))
                        if possible:
                            display_path = possible[0]
                        else:
                            display_path = cand_path
                except Exception:
                    display_path = Path(r['source'])

            # Render the displayed file path as an anchor that opens in a new tab when possible
            try:
                if display_path.exists():
                    try:
                        rel = display_path.resolve().relative_to(Path.cwd().resolve())
                        http_url = f"http://localhost:{STATIC_SERVER_PORT}/{quote(rel.as_posix())}"
                    except Exception:
                        http_url = None

                    if http_url:
                        safe_text = _html.escape(str(display_path))
                        st.markdown(f"**Path:** <a href=\"{http_url}\" target=\"_blank\">{safe_text}</a>", unsafe_allow_html=True)
                    else:
                        file_uri = display_path.resolve().as_uri()
                        safe_text = _html.escape(str(display_path))
                        st.markdown(f"**Path:** <a href=\"{file_uri}\" target=\"_blank\">{safe_text}</a>", unsafe_allow_html=True)
                else:
                    # If the file doesn't exist locally, still attempt to make an http URL
                    try:
                        rel = Path(r['source']).resolve().relative_to(Path.cwd().resolve())
                        http_url = f"http://localhost:{STATIC_SERVER_PORT}/{quote(rel.as_posix())}"
                        safe_text = _html.escape(str(Path(r['source'])))
                        st.markdown(f"**Path:** <a href=\"{http_url}\" target=\"_blank\">{safe_text}</a>", unsafe_allow_html=True)
                    except Exception:
                        st.markdown(f"**Path:** {display_path}")
            except Exception:
                st.markdown(f"**Path:** {display_path}")

            # Button that opens the file with the default local application
            try:
                if display_path.exists():
                    b1, b2, _ = st.columns([0.15, 0.2, 0.65])
                    if b1.button("📂 Ouvrir", key=f"open_{r['source']}"):
                        _open_local(display_path)
                    if b2.button("🔎 Afficher dans le Finder", key=f"reveal_{r['source']}"):
                        _open_local(display_path, reveal=True)
            except Exception as e:
                st.warning(f"Impossible d'ouvrir le fichier : {e}")

            # Show YAML contents inline (no metadata link) inside a collapsible 'Metadata' expander
            if r.get('yaml_source'):
                try:
                    yp = Path(r['yaml_source'])
                    found = None
                    if yp.exists():
                        found = yp
                    else:
                        possible = list(Path('./data').rglob(yp.name))
                        if possible:
                            found = possible[0]

                    if found:
                        try:
                            yaml_text = found.read_text(encoding='utf-8', errors='ignore')
                            max_preview = 200 * 1024
                            preview = (yaml_text[:max_preview] + '\n\n... (truncated)') if len(yaml_text) > max_preview else yaml_text
                            with st.expander("Metadata", expanded=False):
                                st.code(preview, language='yaml')
                        except Exception:
                            # If reading fails, show a plain text fallback inside the expander
                            with st.expander("Metadata", expanded=False):
                                st.write("(Unable to read YAML contents)")
                except Exception:
                    # If any of the above fails, just skip inline metadata preview
                    pass

            # (Path already rendered above)

st.markdown("---")
st.caption("This app uses sentence-transformers/all-MiniLM-L6-v2 for embeddings and a persisted nearest-neighbors index in ./storage.")
