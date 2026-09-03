import os
import chromadb
from chromadb.utils import embedding_functions
from app.config import CHROMA_PATH

embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="assistant_docs", embedding_function=embed_fn)

def chunk_text(text: str, chunk_size=800, overlap=120) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks

def ingest_document(doc_id: str, text: str):
    chunks = chunk_text(text)
    collection.add(
        documents=chunks,
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        metadatas=[{"source": doc_id} for _ in chunks],
    )

def ingest_docs_folder(folder="docs"):
    if not os.path.isdir(folder):
        return
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if os.path.isfile(path) and filename.endswith((".txt", ".md")):
            with open(path, "r", encoding="utf-8") as f:
                ingest_document(filename, f.read())

def retrieve(query: str, k=4) -> list[tuple[str, dict]]:
    if collection.count() == 0:
        return []
    res = collection.query(query_texts=[query], n_results=min(k, collection.count()))
    return list(zip(res["documents"][0], res["metadatas"][0]))