import os
import requests
from loguru import logger
from opik import track

from google import genai
from .ingestion import qdrant_client, COLLECTION_NAME

# Reuse GenAI client from ingestion
genai_client = genai.Client()

@track
def retrieve_qdrant(query: str, top_k: int = 3) -> list[dict]:
    """Retrieve top-k relevant chunks from Qdrant using vector similarity."""
    logger.info(f"Embedding query: '{query}'")
    response = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=[query],
    )
    query_vector = response.embeddings[0].values
    
    logger.info("Executing vector search in Qdrant...")
    search_result = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )
    
    results = []
    for hit in search_result.points:
        # hit.payload contains 'text' and 'source'
        results.append({
            "score": hit.score,
            "text": hit.payload["text"],
            "source": hit.payload["source"]
        })
    logger.info(f"Retrieved {len(results)} chunks from Qdrant.")
    return results

@track
def fallback_to_web(query: str, num_results: int = 3) -> list[dict]:
    """Fallback to web search using Serper.dev API when vector results are irrelevant."""
    logger.info("Triggering Serper Web Search Fallback mechanism...")
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY environment variable is not set!")
    
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": num_results
    }
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    results = []
    if "organic" in data:
        for item in data["organic"][:num_results]:
            results.append({
                "source": item.get("link", "web"),
                "text": item.get("snippet", "")
            })
    logger.info(f"Retrieved {len(results)} web snippets via Serper.")
    return results
