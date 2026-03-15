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
def process_local_docs() -> list[dict]:
    """Processes all .md and .pdf files in the data/ directory, parses via Docling, chunks via HybridChunker."""
    data_dir = Path("data")
    chunks = []
    
    if not data_dir.exists() or not data_dir.is_dir():
        logger.warning(f"Data directory '{data_dir}' not found. Returning empty chunks.")
        return chunks
        
    # Find all .md and .pdf files
    valid_extensions = {".md", ".pdf"}
    files_to_process = [f for f in data_dir.iterdir() if f.suffix.lower() in valid_extensions and f.is_file()]
    
    if not files_to_process:
        logger.info(f"No valid documents found in {data_dir}. Place .md or .pdf files there.")
        return chunks
        
    logger.info(f"Found {len(files_to_process)} documents to process in {data_dir}.")
    
    converter = DocumentConverter()
    chunker = HybridChunker()
    
    for file_path in files_to_process:
        logger.info(f"Parsing document: {file_path.name}")
        try:
            result = converter.convert(str(file_path))
            doc = result.document
            
            logger.info(f"Chunking document: {file_path.name}")
            chunk_iter = chunker.chunk(doc)
            
            for idx, chunk in enumerate(chunk_iter):
                chunks.append({
                    "id": f"{file_path.stem}_{idx}",
                    "text": chunk.text,
                    "source": file_path.name
                })
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            
    logger.info(f"Produced a total of {len(chunks)} chunks from all documents.")
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
                id=i,  # Qdrant requires integer or UUID string IDs
                vector=embedding_obj.values,
                payload={"text": chunk["text"], "source": chunk["source"], "chunk_id": chunk["id"]}
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
    chunks = process_local_docs()
    if chunks:
        embed_and_store(chunks)
    else:
        logger.warning("No chunks to store. Vector store is empty.")

def get_qdrant_client() -> QdrantClient:
    return qdrant_client

if __name__ == "__main__":
    run_ingestion()
