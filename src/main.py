import os
import sys
from loguru import logger
from opik import track

from src.ingestion import run_ingestion
from src.retrieval import retrieve_qdrant, fallback_to_web
from src.evaluator import evaluate_relevance
from src.generation import iterative_generation

# Setup loguru
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Add file logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger.add(f"{LOG_DIR}/pipeline.log", rotation="10 MB", retention="10 days", level="INFO")

@track
def run_crag_pipeline(query: str) -> str:
    """End-to-end pipeline execution."""
    logger.info(f"--- Starting Pipeline for Query: '{query}' ---")
    
    # 1. Retrieve Qdrant Base Context
    qdrant_chunks = retrieve_qdrant(query)
    
    if not qdrant_chunks:
        logger.warning("No chunks found in Qdrant. Falling back to Web.")
        active_chunks = fallback_to_web(query)
    else:
        # 2. Fact-Checker CRAG Evaluator -> Route fallback Serper if needed.
        eval_result = evaluate_relevance(query, qdrant_chunks)
        
        if eval_result.status == "correct":
            logger.info("CRAG Result: CORRECT. Using local Qdrant chunks.")
            active_chunks = qdrant_chunks
        elif eval_result.status == "ambiguous":
            logger.info("CRAG Result: AMBIGUOUS. Merging local chunks with Serper Web fallback.")
            web_chunks = fallback_to_web(query)
            active_chunks = qdrant_chunks + web_chunks
        else:
            logger.warning("CRAG Result: INCORRECT. Falling back to Serper Web Search ONLY.")
            logger.warning(f"Reasoning: {eval_result.reasoning}")
            active_chunks = fallback_to_web(query)
            
    # 3. Formatted Sub-Context Array -> Generation Draft
    # 4. Editor Critic -> Feedback loop while Grounding < 0.8
    # 5. Yield final text
    final_answer = iterative_generation(query, active_chunks)
    
    logger.info("--- Pipeline Execution Complete ---")
    return final_answer

if __name__ == "__main__":
    import sys
    
    # Ensure environment variables are loaded if using python-dotenv, otherwise assume they are set
    logger.info("Initializing vector store before running pipeline...")
    run_ingestion()
    
    # Check for CLI arguments
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # Default test query
        query = "What are the core components of the corrective self reflective RAG repository?"
        
    answer = run_crag_pipeline(query)
    
    print("\n================ FINAL ANSWER ================\n")
    print(answer)
