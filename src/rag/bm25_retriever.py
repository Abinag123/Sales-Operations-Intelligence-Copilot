from rank_bm25 import BM25Okapi

from src.rag.chunking import all_chunks


# ==========================================
# 1. PREPARE DOCUMENT COLLECTION
# ==========================================

documents = []

for chunk in all_chunks:

    documents.append({
        "content": chunk["content"],
        "source": chunk["source"],
        "chunk_id": chunk["chunk_id"]
    })

print("Total documents:", len(documents))


# ==========================================
# 2. TOKENIZE DOCUMENTS
# ==========================================

tokenized_documents = [
    doc["content"].lower().split()
    for doc in documents
]


# ==========================================
# 3. BUILD BM25 INDEX
# ==========================================

bm25 = BM25Okapi(tokenized_documents)

print("BM25 index created successfully!")


# ==========================================
# 4. KEYWORD SEARCH FUNCTION
# ==========================================

def bm25_search(query, top_k=3):

    query_tokens = query.lower().split()

    scores = bm25.get_scores(query_tokens)

    ranked_indices = scores.argsort()[::-1][:top_k]

    results = []

    for index in ranked_indices:

        score = float(scores[index])

        if score <= 0:
            continue

        doc = documents[index]

        results.append({
            "content": doc["content"],
            "source": doc["source"],
            "chunk_id": doc["chunk_id"],
            "bm25_score": round(score, 4)
        })

    return results


# ==========================================
# 5. TEST BM25 RETRIEVAL
# ==========================================

if __name__ == "__main__":

    questions = [
        "Lead Generation",
        "discount approval",
        "Digital Marketing services",
        "customer quotations"
    ]

    for question in questions:

        print("\n" + "=" * 60)
        print("QUESTION:", question)
        print("=" * 60)

        results = bm25_search(question, top_k=3)

        for i, result in enumerate(results, start=1):

            print(f"\nResult {i}")
            print("Source:", result["source"])
            print("Chunk ID:", result["chunk_id"])
            print("BM25 Score:", result["bm25_score"])
            print("Content:", result["content"])