# Project scripts reference

This document describes the scripts and utilities in this repository, how to run them, and what they produce. It is intended as a living reference so you can keep the code organized and reproducible.

## Conventions
- Scripts that are intended as CLI tools live at the project root (e.g. `index_and_query.py`).
- Small helper scripts live under `scripts/` and are targeted at maintenance, testing, or the UI (Streamlit).
- `esms/` contains the canonical ESMS YAML templates. `metadata/` contains generated metadata YAMLs for each artifact.

---

## Top-level scripts

### `esms_llm_metadata.py`
Purpose: Generate ESMS-formatted YAML metadata for artifacts by calling an LLM per ESMS section and writing one YAML per artifact under `./metadata`.

Typical usage:
```
python esms_llm_metadata.py --root ./data --esms-vocab-dir ./esms --preview 1
```

Notes:
- Requires LLM credentials via environment variables (e.g. `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_MODEL` or LM Studio equivalents).
- The script preserves identity fields (title/path) and writes LLM outputs into the metadata directory. See headers in the file for more options.

### `index_and_query.py`
Purpose: Build a persistent semantic index (llama-index) over files in `./data` and `./metadata` using a local sentence-transformers adapter. Persists artifacts to `./storage`.

Typical usage:
```
python index_and_query.py
```

Important environment flags:
- `SAMPLE_LIMIT` — limit the number of files to index (useful for testing).
- `SHOW_PROGRESS` — show encoding progress bar.
- `EMB_BATCH_SIZE` — batching size used when embedding documents.

Notes:
- This project requires `llama-index` as the index engine and uses `sentence-transformers` locally for embeddings (model `all-MiniLM-L6-v2` by default).

### `ingest.py`
Purpose: Content ingestion helper. Reads files from `./data`, extracts text (PDF, DOCX, etc.) and prepares documents for indexing.

Typical usage: inspect file; this script is imported by `index_and_query.py` in the pipeline.

### `llm_test_connection.py`
Purpose: Quick script to verify LLM connectivity and authentication. Prints model id or service response.

Typical usage:
```
python llm_test_connection.py
```

### `apply_esms_with_lmstudio.py`, `apply_llm_suggestions.py`
Purpose: Variations and helpers to run ESMS metadata application via different LLM endpoints or to apply LLM suggestions to existing metadata. See inline comments for options.

### `rag.py`
Purpose: A retrieval-augmented generation example script; demonstrates retrieving documents from the index and generating an LLM answer using retrieved context.

---

## `scripts/` utilities

### `scripts/streamlit_search.py`
Purpose: Streamlit web UI for searching the index. Presents a sidebar search box and options to show all indexed results. Uses `./storage` artifacts (`meta.json`, `nbrs.pkl`, `embeddings.npy`) and `sentence-transformers` for query embeddings.

Run (from project root):
```
python -m streamlit run scripts/streamlit_search.py --server.port 8501 --server.headless true
```

Notes: the app uses cached model loading and resolves metadata YAMLs to present the best display title and the original artifact path.

### `scripts/run_sample_query.py`
Purpose: Small script to load `meta.json` and `nbrs.pkl` and run a nearest-neighbor query from the command line — useful for smoke tests and CI checks.

Usage:
```
python scripts/run_sample_query.py
```

### `scripts/query_index.py`, `scripts/wait_for_index.py`, `scripts/probe_storage.py`, `scripts/probe_llama_imports.py`
Purpose: Helper/utility scripts for testing imports, waiting for index artifacts to appear, and running quick interactive queries.

---

## Notebooks

- `llamaindex_vector_stores.ipynb` — experiments with vector stores and llama-index internals.
- `rag_test.ipynb` — exploratory RAG notebook.

Notebooks are for exploration — keep them for reference but they may contain large outputs and are not required for the production pipeline.

---

## Templates and metadata

- `esms/` — contains the six ESMS YAML templates used as canonical structure. Do not modify these unless you intend to change the schema.
- `metadata/` — generated YAML metadata per artifact. These are the outputs of `esms_llm_metadata.py` and are used by the index.

If you want to re-generate metadata, delete selective `metadata/` files and re-run `esms_llm_metadata.py` with the appropriate flags.

---

## Reorganization suggestions

1. Create a `src/` directory for production scripts (move `esms_llm_metadata.py`, `index_and_query.py`, `ingest.py`, `rag.py`, etc.). Keep `scripts/` for utilities and `notebooks/` for experimentation.
2. Add per-script README headers (short usage examples) — this document covers them but adding inline module docstrings helps IDEs and readers.
3. Keep `data/` and `backup/` out of git (we updated `.gitignore` accordingly). If you want a small sample dataset for CI or testing, create `data/sample/` and track only that.

---

## Next steps I can take for you (pick any)

1. Generate `docs/SCRIPTS.md` (done) and also insert header docstrings into every top-level script (I can add them in-place).
2. Physically move selected scripts into `src/` and update imports/CLI entry points (I will prepare a preview before committing moves).
3. Create a per-script markdown file under `docs/` with expanded examples and options for each script.

Tell me which next step you'd like and I'll continue.
