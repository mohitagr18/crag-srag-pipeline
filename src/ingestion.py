import os
import requests
from pathlib import Path
from loguru import logger
from opik import track

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from google import genai
from google.genai import types

# Setup GenAI client - automatically picks up GEMINI_API_KEY from env
genai_client = genai.Client()

# Initialize Qdrant client globally for the single-threaded in-memory session.
# We will expose it to other modules via getter methods if needed, but for simplicity
# we can just use a singleton pattern or export it.
qdrant_client = QdrantClient(":memory:")
COLLECTION_NAME = "github_repo_collection"

def init_qdrant():
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        logger.info(f"Initialized new Qdrant collection: {COLLECTION_NAME}")

@track
def fetch_and_process_repo_docs() -> list[dict]:
    """Fetches README from github, parses via Docling, chunks via HybridChunker."""
    repo_url = "https://raw.githubusercontent.com/sourangshupal/corrective_self_reflective_rag/main/README.md"
    local_path = "repo_README.md"
    
    if not os.path.exists(local_path):
        logger.info(f"Downloading repo documentation from {repo_url}")
        resp = requests.get(repo_url)
        resp.raise_for_status()
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(resp.text)
    
    logger.info("Parsing document with Docling DocumentConverter")
    converter = DocumentConverter()
    result = converter.convert(local_path)
    doc = result.document
    
    logger.info("Chunking using HybridChunker")
    chunker = HybridChunker()
    chunk_iter = chunker.chunk(doc)
    
    chunks = []
    for idx, chunk in enumerate(chunk_iter):
        chunks.append({
            "id": idx,
            "text": chunk.text,
            "source": local_path
        })
    
    logger.info(f"Produced {len(chunks)} chunks.")
    return chunks

@track
def embed_and_store(chunks: list[dict]):
    """Embeds text chunks via Google GenAI and stores them in Qdrant in-memory."""
    texts = [chunk["text"] for chunk in chunks]
    
    logger.info(f"Generating embeddings for {len(texts)} chunks via Google GenAI...")
    # GenAI embed_content supports batch processing natively
    response = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
    )
    
    embeddings = response.embeddings
    
    logger.info("Upserting to Qdrant...")
    points = []
    for i, (chunk, embedding_obj) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=i,
                vector=embedding_obj.values,
                payload={"text": chunk["text"], "source": chunk["source"]}
            )
        )
    
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    logger.info(f"Successfully upserted {len(points)} chunks into Qdrant in-memory store.")

def run_ingestion():
    """Builds the vector store index."""
    init_qdrant()
    chunks = fetch_and_process_repo_docs()
    embed_and_store(chunks)

def get_qdrant_client() -> QdrantClient:
    return qdrant_client

if __name__ == "__main__":
    run_ingestion()
