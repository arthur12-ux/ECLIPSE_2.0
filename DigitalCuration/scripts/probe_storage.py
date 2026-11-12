"""scripts/probe_storage.py

Probe modules under `llama_index` to locate storage and service-related symbols.

Usage:
    python scripts/probe_storage.py
"""

import importlib, pkgutil
import llama_index

names_to_find = ['StorageContext', 'load_index_from_storage', 'load_index_from_storage', 'ServiceContext']
print('iterating modules under llama_index')
for finder, name, ispkg in pkgutil.iter_modules(llama_index.__path__):
    modname = f'llama_index.{name}'
    try:
        mod = importlib.import_module(modname)
        for n in names_to_find:
            if hasattr(mod, n):
                print(modname, 'has', n)
    except Exception as e:
        print('could not import', modname, '->', e)

# Also check core
try:
    import llama_index.core as core
    print('core has:', [n for n in dir(core) if n in names_to_find])
except Exception as e:
    print('core import failed', e)
