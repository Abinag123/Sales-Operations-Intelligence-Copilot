from sentence_transformers import SentenceTransformer
from src.rag.chunking import all_chunks

# 1. Load embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded!")

# 2. Extract text from chunks
texts = [chunk["content"] for chunk in all_chunks]

# 3. Generate embeddings
print("\nGenerating embeddings...")

embeddings = model.encode(
    texts,
    show_progress_bar=True
)

# 4. Display results
print("\nEmbedding generation completed!")

print("Total chunks:", len(texts))
print("Embedding shape:", embeddings.shape)
print("Vector dimensions:", len(embeddings[0]))

# 5. Display first embedding
print("\nFirst embedding preview:")
print(embeddings[0][:10])