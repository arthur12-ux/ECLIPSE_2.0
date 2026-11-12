"""scripts/wait_for_index.py

Wait for `./storage` index artifacts to appear and run a simple smoke-test query.

Usage:
    python scripts/wait_for_index.py
Environment:
    Uses environment vars SAMPLE_QUERY, WAIT_TIMEOUT, POLL_INTERVAL optionally.
"""

import time, os, glob, json, pickle
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

PERSIST_DIR = 'storage'
WAIT_TIMEOUT = int(os.environ.get('WAIT_TIMEOUT', '3600'))  # seconds
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '5'))

start = time.time()
print('Waiting for index artifacts in', PERSIST_DIR)
while True:
    if os.path.exists(os.path.join(PERSIST_DIR, 'embeddings.npy')) and os.path.exists(os.path.join(PERSIST_DIR, 'meta.json')):
        print('Found embeddings.npy and meta.json')
        break
    if time.time() - start > WAIT_TIMEOUT:
        print('Timeout waiting for index artifacts')
        raise SystemExit(2)
    time.sleep(POLL_INTERVAL)

files = sorted(glob.glob(os.path.join(PERSIST_DIR, '*')))
print('Storage files:')
for f in files:
    print(' -', f)

# Load persisted index and run a sample query
meta = json.load(open(os.path.join(PERSIST_DIR, 'meta.json'), 'r', encoding='utf-8'))
embs = None
nbrs = None
if os.path.exists(os.path.join(PERSIST_DIR, 'embeddings.npy')):
    embs = np = None
    try:
        import numpy as np
        embs = np.load(os.path.join(PERSIST_DIR, 'embeddings.npy'))
    except Exception as e:
        print('Could not load embeddings.npy:', e)

if os.path.exists(os.path.join(PERSIST_DIR, 'nbrs.pkl')):
    try:
        with open(os.path.join(PERSIST_DIR, 'nbrs.pkl'), 'rb') as f:
            nbrs = pickle.load(f)
    except Exception as e:
        print('Could not load nbrs.pkl:', e)

# If nearest neighbors available, run a sample query
model = SentenceTransformer('all-MiniLM-L6-v2')
q = os.environ.get('SAMPLE_QUERY', 'lunar habitat')
print('\nRunning sample query:', q)
q_emb = model.encode([q])
if nbrs is not None:
    d, idx = nbrs.kneighbors(q_emb, n_neighbors=5)
    for dist, i in zip(d[0], idx[0]):
        print(f'score={(1-dist):.3f} source={meta[i]["source"]}')
else:
    print('No nbrs.pkl found, cannot run local nearest-neighbors sample. If llama-index persisted files are present, load them with llama-index in a separate step.')
