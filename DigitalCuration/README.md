
# digitalCuration — User Guide and Usage Instructions

About this product
-------------------
digitalCuration is a local, user-oriented tool that helps you create structured, searchable metadata for a collection of files and then search those files with semantic queries. The product uses a language model (LLM) to populate ESMS-compliant metadata for each artifact and a local embedding model to build a semantic index for fast, relevance-aware search. The intended audience for this guide is someone who wants to run the system and use its outputs; no development, code changes, or deep Python knowledge are required to follow the steps below.

High-level workflow
-------------------
At a high level, the system follows these steps: you provide a directory of files to the pipeline; optionally, the product will call a configured LLM to generate one ESMS YAML metadata file per artifact; next the pipeline extracts text from your files and metadata and computes vector embeddings locally; finally the product persists the index and offers a small Streamlit web application that allows interactive querying and inspection of results. Each step is described in detail in the sections below.

Getting started (requirements and environment)
---------------------------------------------
To run digitalCuration you need a Windows machine with PowerShell and Python 3.8 or later (3.11 is recommended). The product is distributed as source code and uses a Python virtual environment to isolate dependencies. The recommended one-time setup is to create a virtual environment in the repository folder, activate it for your session, and install the Python packages required by the project. These commands will accomplish that; they are intended for a PowerShell terminal opened in the repository root.

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If any package fails to install (for example packages that depend on compiled libraries), please capture the error text and share it; common fixes include upgrading pip and retrying or installing a binary wheel provided by the package maintainers.

LLM usage and configuration (optional)
-------------------------------------
The metadata generation step uses an LLM to create human-readable and ESMS-structured fields (descriptions, keywords, summaries, etc.). This step is optional — you can use the product to search pre-existing metadata or to index raw files without LLM-generated metadata. If you decide to run metadata generation, you must provide an API key for a compatible LLM endpoint. The software expects OpenAI-compatible environment variables; in PowerShell you can set them for the current session using `$env:`. If you run a local LM Studio instance, set `OPENAI_API_BASE` to the instance URL. If you do not set these environment variables and attempt a full metadata generation, the script will fail with authentication errors; use preview mode first to validate behavior without calling the LLM.

Example configuration (PowerShell):

```powershell
$env:OPENAI_API_KEY = 'sk-REPLACE_WITH_YOUR_KEY'
# Optional: if using LM Studio or a custom OpenAI-compatible host, point to it
$env:OPENAI_API_BASE = 'https://your-lmstudio-instance/api'  # optional
$env:OPENAI_MODEL = 'openai/gpt-oss-20b'                     # optional override
```

Generating ESMS metadata for your files
--------------------------------------
The metadata generator will discover files in the `data/` folder, preserve each artifact's title and path, and produce a single ESMS YAML file per artifact under the `metadata/` folder. The generator provides a safe "preview" mode; this mode performs all the discovery and prompt preparation steps without contacting the LLM provider. Use preview mode to confirm how many items will be processed and to inspect the prompts that would be sent. When you are ready to produce metadata files, run the full generation command. Be aware that generating metadata at scale will make API calls and may incur costs depending on your model provider.

Preview (does not write files):

```powershell
.\.venv\Scripts\python.exe esms_llm_metadata.py --root ./data --esms-vocab-dir ./esms --preview 1
```

Full run (writes YAML files to `metadata/`):

```powershell
.\.venv\Scripts\python.exe esms_llm_metadata.py --root ./data --esms-vocab-dir ./esms
```

Indexing: building the semantic search store
------------------------------------------
After you have metadata (either generated or pre-existing), you can build the semantic index. The indexing step extracts text from files and metadata, computes vector embeddings locally using the `sentence-transformers` model `all-MiniLM-L6-v2`, and constructs a persisted nearest-neighbors structure. Index artifacts are written to the `storage/` folder and include files such as `embeddings.npy`, `nbrs.pkl`, and `meta.json`. Indexing a large collection may take time and require modest CPU/memory resources; for rapid testing you can restrict the run to a small sample set.

Quick test (limit indexing to few items):

```powershell
$env:SAMPLE_LIMIT = 3
.\.venv\Scripts\python.exe index_and_query.py
```

Full index build (process all items):

```powershell
.\.venv\Scripts\python.exe index_and_query.py
```

When the indexing step finishes, confirm that the `storage/` folder was created and contains the index artifacts described above. You can copy `storage/` and `metadata/` to another machine if you want to run the Streamlit UI elsewhere without rebuilding the index.

Running the Streamlit web app and using the UI
--------------------------------------------
The repository contains a small Streamlit app that provides an interactive search interface over the persisted nearest-neighbors index. Start the app in PowerShell and then point your browser to http://localhost:8501. The app has a sidebar for entering queries and controls, and the main area shows search results with short snippets and links to metadata files when available.

Start Streamlit locally with this command:

```powershell
.\.venv\Scripts\python.exe -m streamlit run scripts/streamlit_search.py --server.port 8501 --server.headless false
```

The UI is intentionally simple: enter a question or a search phrase in the sidebar, submit, and the app will display the top matches with basic context. If you need additional features (highlighting, more detailed provenance, or result filtering), those can be added; tell me which features you prefer and I will implement them.

Local file links and inline metadata preview
-------------------------------------------
The Streamlit UI now includes an inline, syntax-highlighted preview of the YAML metadata for results (look for the "Metadata" expander inside each result). For clickable links to files and metadata to work reliably in your browser, you can run a tiny local static server that serves repository files over HTTP — this avoids browser restrictions on file:// links.

Start the helper server in a separate terminal (optional but recommended):

```powershell
.\.venv\Scripts\python.exe scripts\serve_data.py --port 8502
```

When the helper server is running the Streamlit UI will link to resources via http://localhost:8502/..., which most browsers will open without blocking. If you prefer not to run the helper server, the UI will still attempt to produce file:// links as a fallback, but some browsers may block those clicks.

Troubleshooting and common issues
---------------------------------
If you encounter package or import errors, verify that the virtual environment is active (`.venv`), and reinstall the requirements with `pip install -r requirements.txt`. Some packages, particularly those that depend on PyTorch or compiled extensions, may need platform-specific wheels—if installation fails, copy the terminal output and I will suggest a remedy.

If the Streamlit UI launches but shows no results, first check whether the index artifacts exist in `storage/` (especially `meta.json` and `nbrs.pkl`). If they are missing or corrupted, re-run the indexing step to recreate them. For long-running failures during indexing, run the script with `SAMPLE_LIMIT` to gather a shorter failure trace that is easier to debug.

If the metadata generator reports authentication errors, re-check the `OPENAI_API_KEY` environment variable and the `OPENAI_API_BASE` if you are using a local LM Studio instance. Use preview mode to validate the generator's prompts before running a full generation to avoid unnecessary API usage.

Privacy, security, and cost considerations
----------------------------------------
The product is meant to run locally. However, if you enable LLM-based metadata generation, content is sent to the model provider (OpenAI or a compatible instance) as part of the prompt. This may expose sensitive information if your documents contain secrets or regulated data. For sensitive workloads, consider using a private LLM deployment (for example LM Studio running on your network) or disable automatic generation and provide metadata manually. Also monitor API usage and cost while performing large-scale generation runs.

Distribution and next steps
-------------------------
If you plan to distribute the tool to users who are not comfortable running commands, I can prepare several packaging options: a single run-all script that automates environment setup and runs the pipeline; a Docker image that bundles Python, the dependencies, and prebuilt index artifacts; or a packaged executable for Windows. Each option has trade-offs (ease of use vs. size and maintainability). Tell me which distribution format you prefer and whether you want `storage/` and `metadata/` pre-populated in the distribution.

Run with Docker Compose
-----------------------
If you prefer to run the product inside containers, `docker compose` offers a convenient, repeatable way to build and run the application. A `docker-compose.yml` is included in this repository. The general steps are:

1. Create a copy of the example environment file and fill in any values required by your environment (do not commit secrets):

```powershell
Copy-Item .env.example .env
# Edit .env in a text editor and add your OPENAI_API_KEY (if you plan to use the LLM features)
```

2. Build the image and start the service using Docker Compose from the repository root:

```powershell
docker compose up --build
```

This command will build the Docker image (using `Dockerfile`) and start the Streamlit application. The Streamlit app will be available on your host at `http://localhost:8501`.

Notes:
- The compose setup mounts the repository `storage/` and `metadata/` directories into the container so the index and metadata persist on your host.
- Provide sensitive values (for example `OPENAI_API_KEY`) via the `.env` file or your shell environment; do not commit secrets to the repository.
- To stop the service, press Ctrl+C in the terminal running `docker compose up`, or run:

```powershell
docker compose down
```


Support and contact
-------------------
If you need help running the product, send the error output and describe which step failed (environment setup, metadata generation, indexing, or Streamlit). If you'd like sample outputs or screenshots to include in this README, specify which artifacts you want shown (for example a sample ESMS YAML and a screenshot of the Streamlit results pane) and I will add them to the repository.

Licensing note
--------------
This repository does not currently include a license file. If you plan to publish the repository publicly, add a permissive license such as MIT or Apache-2.0 to clearly state permitted uses and limitations.

File locations and summary
--------------------------
The most relevant locations in the repository are the following: `data/` contains your source artifacts; `metadata/` will hold generated ESMS YAML files (one per artifact); `storage/` contains the index and embedding artifacts used by the Streamlit UI; `scripts/streamlit_search.py` is the web application; and `src/` contains the production Python modules if you need to investigate or extend the code.
Additional scripts:
- `scripts/serve_data.py` — optional tiny static server that serves the repository root on localhost (default port 8502). Start this if you want Streamlit links to open reliably in your browser.

