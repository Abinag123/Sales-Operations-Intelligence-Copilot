from src.rag.retriever import search_documents
from src.llm.ollama_client import LLMUnavailable, generate_response


def ask_company_assistant(question):

    # 1. Retrieve relevant company documents
    retrieved_docs = search_documents(
        query=question,
        top_k=3
    )

    if not retrieved_docs:
        return {
            "question": question,
            "answer": "I couldn't find relevant information in the company documents.",
            "llm": "not-called",
            "citations": []
        }

    # 2. Build context for the LLM
    context_parts = []

    for i, doc in enumerate(retrieved_docs, start=1):

        context_parts.append(
            f"""
[Source {i}]
Filename: {doc['source']}
Chunk ID: {doc['chunk_id']}
Content:
{doc['content']}
"""
        )

    context = "\n".join(context_parts)

    # 3. Grounded prompt
    prompt = f"""
You are a professional company knowledge assistant.

Answer the user's question using ONLY the company context below.

Rules:
1. Do not invent company information.
2. If the answer is unavailable, clearly say so.
3. Keep the answer professional and concise.
4. Cite supporting sources using their exact labels,
   such as [Source 1] or [Source 2].
5. Do not cite a source unless it supports the claim.

COMPANY CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    # 4. Generate answer
    #    When the model runtime is unreachable (e.g. a hosted deployment without
    #    Ollama) fall back to the retrieved passages instead of failing the call.
    try:

        answer = generate_response(prompt)

        llm_status = "answered"

    except LLMUnavailable as error:

        print(f"[rag] language model unavailable: {error}")

        answer = (
            "The language model is not reachable from this deployment, so no "
            "generated answer is available. The retrieved company passages "
            "below contain the source material for this question."
        )

        llm_status = "unavailable"

    # 5. Prepare detailed citations
    citations = []

    for i, doc in enumerate(retrieved_docs, start=1):

        citations.append({
            "citation": f"Source {i}",
            "filename": doc["source"],
            "chunk_id": doc["chunk_id"],
            "distance": doc["distance"],
            "supporting_text": doc["content"]
        })

    return {
        "question": question,
        "answer": answer,
        "llm": llm_status,
        "citations": citations
    }


if __name__ == "__main__":

    question = "What services does the company offer?"

    result = ask_company_assistant(question)

    print("\n" + "=" * 65)
    print("COMPANY KNOWLEDGE ASSISTANT")
    print("=" * 65)

    print("\nQUESTION:")
    print(result["question"])

    print("\nAI ANSWER:")
    print(result["answer"])

    print("\nDETAILED SOURCE CITATIONS:")

    for citation in result["citations"]:

        print("\n" + "-" * 50)

        print("Citation:", citation["citation"])
        print("Filename:", citation["filename"])
        print("Chunk ID:", citation["chunk_id"])
        print("Distance:", citation["distance"])

        print("\nSupporting Text:")
        print(citation["supporting_text"])

    print("\n" + "=" * 65)