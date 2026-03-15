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

from src.rewriter import rewrite_query

@track
def run_crag_pipeline(query: str, max_full_loops: int = 2) -> str:
    """End-to-end pipeline execution with Full-Loop Adaptive Retrieval."""
    logger.info(f"--- Starting Pipeline for Query: '{query}' ---")
    
    current_query = query
    for loop in range(max_full_loops):
        if loop > 0:
            logger.info(f"=== FULL LOOP {loop+1}/{max_full_loops}: RE-RETRIEVING WITH REFINED QUERY ===")

        # 1. Retrieve Qdrant Base Context
        qdrant_chunks = retrieve_qdrant(current_query)
        
        if not qdrant_chunks:
            logger.warning(f"No chunks found for '{current_query}'. Falling back to Web.")
            active_chunks = fallback_to_web(current_query)
        else:
            # 2. Fact-Checker CRAG Evaluator
            eval_result = evaluate_relevance(current_query, qdrant_chunks)
            
            if eval_result.status == "correct":
                logger.info("CRAG Result: CORRECT. Using local chunks.")
                active_chunks = qdrant_chunks
            elif eval_result.status == "ambiguous":
                logger.info("CRAG Result: AMBIGUOUS. Merging local chunks with Serper.")
                web_chunks = fallback_to_web(current_query)
                active_chunks = qdrant_chunks + web_chunks
            else:
                logger.warning("CRAG Result: INCORRECT. Falling back to Serper ONLY.")
                active_chunks = fallback_to_web(current_query)
                
        # 3. SR-RAG Generation & Critique
        final_answer, retry_feedback = iterative_generation(current_query, active_chunks)
        
        # 4. If SR-RAG failed to produce grounded answer, rewrite query and loop back
        if retry_feedback and loop < max_full_loops - 1:
            logger.error(f"SR-RAG failure detected: {retry_feedback}")
            current_query = rewrite_query(query, retry_feedback)
            continue
        else:
            # Succes or reached limit
            if retry_feedback:
                logger.warning("Max full loops reached. Returning best effort answer.")
                return "I am sorry, but after multiple retrieval attempts I could not generate a reliably grounded answer."
            
            logger.info("--- Pipeline Execution Complete ---")
            return final_answer

    return "System Error in pipeline loop."

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
