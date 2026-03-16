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
    
    search_query = query
    for loop in range(max_full_loops):
        if loop > 0:
            logger.info(f"=== FULL LOOP {loop+1}/{max_full_loops}: RE-RETRIEVING WITH REFINED QUERY ===")

        # 1. Retrieve Qdrant Base Context
        qdrant_chunks = retrieve_qdrant(search_query)
        
        if not qdrant_chunks:
            logger.warning(f"No chunks found for '{search_query}'. Falling back to Web.")
            active_chunks = fallback_to_web(search_query)
        else:
            # 2. Fact-Checker CRAG Evaluator
            eval_result = evaluate_relevance(search_query, qdrant_chunks)
            
            if eval_result.status == "correct":
                logger.info("CRAG Result: CORRECT. Using local chunks.")
                active_chunks = qdrant_chunks
            elif eval_result.status == "ambiguous":
                logger.info("CRAG Result: AMBIGUOUS. Merging local chunks with Serper.")
                web_chunks = fallback_to_web(search_query)
                active_chunks = qdrant_chunks + web_chunks
            else:
                logger.warning("CRAG Result: INCORRECT. Falling back to Serper ONLY.")
                active_chunks = fallback_to_web(search_query)
                
        # 3. SR-RAG Generation & Critique 
        # CRITICAL FIX: Always pass the ORIGINAL query to the generator so it doesn't drift.
        final_answer, eval_result = iterative_generation(query, active_chunks)
        
        # 4. If SR-RAG failed to produce grounded answer, rewrite query and loop back
        if eval_result and loop < max_full_loops - 1:
            logger.error(f"SR-RAG failure detected: {eval_result.reasoning}")
            search_query = rewrite_query(query, eval_result.reasoning)
            continue
        else:
            # Success or reached limit
            if eval_result:
                # If we are here, it means it's either the last loop OR it's a success
                # BEST EFFORT CHECK: If grounding is high (truthful), deliver it even if utility/recall is low.
                if eval_result.score >= 0.8:
                    logger.warning("Max loops reached but answer is grounded. Returning Best-Effort response.")
                    return final_answer
                
                logger.error("Final answer grounding remains low. Returning failure disclaimer.")
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
