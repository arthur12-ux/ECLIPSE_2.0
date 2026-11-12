"""scripts/probe_llama_imports.py

Quick probe to test various import paths for `llama_index` and report which ones succeed.

Usage:
    python scripts/probe_llama_imports.py
"""

import importlib

candidates = [
    'from llama_index import Document, VectorStoreIndex, StorageContext, load_index_from_storage',
    'from llama_index.core import Document, VectorStoreIndex, Settings',
    'from llama_index.schema import Document',
    'from llama_index import StorageContext, load_index_from_storage',
    'from llama_index.embeddings.huggingface import HuggingFaceEmbedding',
    'from llama_index.embeddings import HuggingFaceEmbedding',
]

for c in candidates:
    try:
        exec(c)
        print('OK:', c)
    except Exception as e:
        print('FAILED:', c, '->', type(e).__name__ + ':', e)

# Also list top-level modules under llama_index
try:
    import llama_index
    import pkgutil
    print('\nTop-level modules in llama_index package:')
    for m in pkgutil.iter_modules(llama_index.__path__):
        print(' -', m.name)
except Exception as e:
    print('Could not inspect llama_index package:', e)
