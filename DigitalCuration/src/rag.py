"""rag.py

Small retrieval-augmented generation (RAG) example demonstrating how to
load documents and create/load a vector index using llama-index.

Usage: used as an example or starting point for RAG experiments.
"""

import nest_asyncio
nest_asyncio.apply()

from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex, ServiceContext, StorageContext, load_index_from_storage

docs = SimpleDirectoryReader(input_dir="./data", filename_as_id=True).load_data()

