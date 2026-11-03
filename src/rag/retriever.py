from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. PROJECT PATHS
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHROMA_DIR = PROJECT_ROOT / "data" / "vector_db"


# ==========================================
# 2. LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded!")


# ==========================================
# 3. CONNECT TO CHROMADB
# ==========================================

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_collection(
    name="company_knowledge"
)

print("ChromaDB connected!")
print("Total stored chunks:", collection.count())


# ==========================================
# 4. SEMANTIC SEARCH FUNCTION
# ==========================================

def search_documents(query, top_k=3):

    # Convert user question into an embedding
    query_embedding = model.encode(query).tolist()

    # Search the vector database
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    # Prepare structured retrieval results
    retrieved_documents = []

    for i, document in enumerate(results["documents"][0]):

        retrieved_documents.append({

            "content": document,

            "source": results["metadatas"][0][i]["source"],

            "chunk_id": results["metadatas"][0][i]["chunk_id"],

            "distance": round(
                results["distances"][0][i], 4
            )

        })

    return retrieved_documents


# ==========================================
# 5. TEST RETRIEVAL
# ==========================================

if __name__ == "__main__":

    test_questions = [

        "What services does Triads Future offer?",

        "Who are the target customers?",

        "How should sales leads be prioritized?",

        "Who can approve discounts?",

        "How are customer quotations prepared?"

    ]

    for question in test_questions:

        print("\n" + "=" * 65)

        print("QUESTION:", question)

        print("=" * 65)

        results = search_documents(
            query=question,
            top_k=2
        )

        for i, result in enumerate(results):

            print(f"\nResult {i + 1}")

            print("Source:", result["source"])

            print("Chunk ID:", result["chunk_id"])

            print("Distance:", result["distance"])

            print("Content:", result["content"])