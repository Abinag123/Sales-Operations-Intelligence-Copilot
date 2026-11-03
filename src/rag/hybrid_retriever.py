from src.rag.bm25_retriever import bm25_search
from src.rag.retriever import search_documents


# ==========================================
# 1. RECIPROCAL RANK FUSION
# ==========================================

def reciprocal_rank_fusion(
    semantic_results,
    keyword_results,
    k=60
):

    fused_scores = {}
    document_store = {}

    # Process semantic search rankings
    for rank, doc in enumerate(semantic_results, start=1):

        doc_id = f"{doc['source']}::{doc['chunk_id']}"

        fused_scores[doc_id] = (
            fused_scores.get(doc_id, 0)
            + 1 / (k + rank)
        )

        document_store[doc_id] = doc

    # Process BM25 rankings
    for rank, doc in enumerate(keyword_results, start=1):

        doc_id = f"{doc['source']}::{doc['chunk_id']}"

        fused_scores[doc_id] = (
            fused_scores.get(doc_id, 0)
            + 1 / (k + rank)
        )

        if doc_id not in document_store:
            document_store[doc_id] = doc

    # Sort documents by combined score
    ranked_ids = sorted(
        fused_scores,
        key=fused_scores.get,
        reverse=True
    )

    results = []

    for doc_id in ranked_ids:

        result = document_store[doc_id].copy()

        result["rrf_score"] = round(
            fused_scores[doc_id], 6
        )

        results.append(result)

    return results


# ==========================================
# 2. HYBRID SEARCH
# ==========================================

def hybrid_search(query, top_k=3):

    semantic_results = search_documents(
        query=query,
        top_k=top_k
    )

    keyword_results = bm25_search(
        query=query,
        top_k=top_k
    )

    combined_results = reciprocal_rank_fusion(
        semantic_results,
        keyword_results
    )

    return combined_results[:top_k]


# ==========================================
# 3. TEST HYBRID RETRIEVAL
# ==========================================

if __name__ == "__main__":

    questions = [
        "Lead Generation",
        "discount approval",
        "Digital Marketing services",
        "customer quotations",
        "How should sales leads be prioritized?"
    ]

    for question in questions:

        print("\n" + "=" * 65)
        print("QUESTION:", question)
        print("=" * 65)

        results = hybrid_search(
            query=question,
            top_k=3
        )

        for i, result in enumerate(results, start=1):

            print(f"\nResult {i}")
            print("Source:", result["source"])
            print("Chunk ID:", result["chunk_id"])
            print("RRF Score:", result["rrf_score"])
            print("Content:", result["content"][:250])