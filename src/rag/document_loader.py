from pathlib import Path

# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Company documents folder
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"


def load_txt_documents():
    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        try:
            text = file_path.read_text(encoding="utf-8")

            documents.append({
                "source": file_path.name,
                "content": text
            })

            print(f"Loaded: {file_path.name}")

        except Exception as error:
            print(f"Error loading {file_path.name}: {error}")

    return documents


if __name__ == "__main__":
    docs = load_txt_documents()

    print("\nTotal documents:", len(docs))

    for doc in docs:
        print("\nSource:", doc["source"])
        print("Characters:", len(doc["content"]))
        print("Preview:", doc["content"][:200])