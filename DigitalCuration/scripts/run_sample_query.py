"""scripts/run_sample_query.py

Small smoke-test script that loads persisted nearest-neighbors artifacts
from `./storage` (meta.json, nbrs.pkl) and runs a query using sentence-transformers.

Usage:
    python scripts/run_sample_query.py
Environment:
    Requires `storage/meta.json` and `storage/nbrs.pkl` created by the index build.
"""

import json, os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

PERSIST_DIR = 'storage'
QUERY = os.environ.get('SAMPLE_QUERY', 'lunar habitat')
K = int(os.environ.get('TOP_K', '5'))

meta_path = os.path.join(PERSIST_DIR, 'meta.json')
nbrs_path = os.path.join(PERSIST_DIR, 'nbrs.pkl')
emb_path = os.path.join(PERSIST_DIR, 'embeddings.npy')

if not os.path.exists(meta_path):
    raise SystemExit('meta.json not found in storage')
meta = json.load(open(meta_path,'r',encoding='utf-8'))

if not os.path.exists(nbrs_path):
    raise SystemExit('nbrs.pkl not found in storage')
with open(nbrs_path, 'rb') as f:
    nbrs = pickle.load(f)

model = SentenceTransformer('all-MiniLM-L6-v2')
q_emb = model.encode([QUERY])

print(f"Running query: {QUERY}\nTop {K} matches:")
dists, idxs = nbrs.kneighbors(q_emb, n_neighbors=K)
for dist, idx in zip(dists[0], idxs[0]):
    src = meta[idx]['source']
    score = 1 - dist
    snippet = ''
    try:
        with open(src, 'r', encoding='utf-8', errors='ignore') as fh:
            snippet = fh.read(400).replace('\n',' ')
    except Exception:
        snippet = '(unable to read snippet)'
    print(f"- score={score:.3f} source={src}\n  snippet={snippet}\n")
