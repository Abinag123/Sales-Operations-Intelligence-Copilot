from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.rag.chunking import all_chunks


# 1. Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHROMA_DIR = PROJECT_ROOT / "data" / "vector_db"


# 2. Load embedding model
print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# 3. Generate embeddings
texts = [chunk["content"] for chunk in all_chunks]

embeddings = model.encode(
    texts,
    show_progress_bar=True
)


# 4. Initialize ChromaDB
print("\nInitializing ChromaDB...")

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)


# 5. Create or access collection
collection = client.get_or_create_collection(
    name="company_knowledge",
    metadata={"hnsw:space": "cosine"}
)


# 6. Prepare metadata
ids = [
    f"{chunk['source']}_{chunk['chunk_id']}"
    for chunk in all_chunks
]

metadatas = [
    {
        "source": chunk["source"],
        "chunk_id": chunk["chunk_id"]
    }
    for chunk in all_chunks
]


# 7. Store data
print("\nStoring embeddings in ChromaDB...")

collection.upsert(
    ids=ids,
    documents=texts,
    embeddings=embeddings.tolist(),
    metadatas=metadatas
)


# 8. Verify storage
print("\nStorage completed!")

print("Total stored documents:", collection.count())
print("Database location:", CHROMA_DIR)