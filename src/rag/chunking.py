from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.rag.document_loader import load_txt_documents


# Load company documents
documents = load_txt_documents()

# Configure text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]
)

# Split documents
all_chunks = []

for doc in documents:
    chunks = text_splitter.split_text(doc["content"])

    for index, chunk in enumerate(chunks):
        all_chunks.append({
            "source": doc["source"],
            "chunk_id": index,
            "content": chunk
        })

# Display results
print("\nTotal chunks:", len(all_chunks))

for chunk in all_chunks:
    print("\nSource:", chunk["source"])
    print("Chunk ID:", chunk["chunk_id"])
    print("Characters:", len(chunk["content"]))
    print("Content:\n", chunk["content"])