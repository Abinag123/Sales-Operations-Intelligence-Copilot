"""Rebuild the Chroma knowledge base from data/documents/*.txt.

This loads every company document, chunks it, embeds it with
sentence-transformers/all-MiniLM-L6-v2 and upserts the vectors into
data/vector_db (collection: company_knowledge).

Usage:
    python scripts/ingest_knowledge.py

Re-run whenever a document in data/documents changes.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    print("Rebuilding the company knowledge index...")
    # src/rag/vector_store.py performs the ingestion at import time and is the
    # single source of truth for chunking + embedding + storage.
    runpy.run_module("src.rag.vector_store", run_name="__main__")
    print("\nDone. The API will pick up the refreshed collection on restart.")
