"""scripts/query_index.py

Interactive query helper for the persisted nearest-neighbors index in `./storage`.

Usage:
    python scripts/query_index.py

This script loads `meta.json`, `embeddings.npy`, and `nbrs.pkl` and prompts for a query.
"""

import json
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

PERSIST_DIR = 'storage'

# load metadata and neighbors
with open(f'{PERSIST_DIR}/meta.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)
embs = np.load(f'{PERSIST_DIR}/embeddings.npy')
with open(f'{PERSIST_DIR}/nbrs.pkl', 'rb') as f:
    nbrs = pickle.load(f)

model = SentenceTransformer('all-MiniLM-L6-v2')
q = input('Enter a query: ')
q_emb = model.encode([q])
dists, idxs = nbrs.kneighbors(q_emb, n_neighbors=5)
for dist, idx in zip(dists[0], idxs[0]):
    src = meta[idx]['source']
    print(f"score={(1-dist):.3f} source={src}")
    # print a snippet of the original document file
    try:
        with open(src, 'r', encoding='utf-8', errors='ignore') as f:
            txt = f.read(400).replace('\n', ' ')
            print(' snippet=', txt)
    except Exception:
        print(' snippet: (unable to read source)')
    print()
