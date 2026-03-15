import sys
from loguru import logger
from opik import track

from .ingestion import run_ingestion
from .retrieval import retrieve_qdrant, fallback_to_web
from .evaluator import evaluate_relevance
from .generation import iterative_generation

# Setup loguru
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

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
        
        if eval_result.is_relevant:
            logger.info("CRAG Evaluation Passed. Using Qdrant chunks.")
            active_chunks = qdrant_chunks
        else:
            logger.warning("CRAG Evaluation Failed. Falling back to Serper Web Search.")
            logger.warning(f"CRAG Reasoning: {eval_result.reasoning}")
            active_chunks = fallback_to_web(query)
            
    # 3. Formatted Sub-Context Array -> Generation Draft
    # 4. Editor Critic -> Feedback loop while Grounding < 0.8
    # 5. Yield final text
    final_answer = iterative_generation(query, active_chunks)
    
    logger.info("--- Pipeline Execution Complete ---")
    return final_answer

if __name__ == "__main__":
    # Ensure environment variables are loaded if using python-dotenv, otherwise assume they are set
    logger.info("Initializing vector store before running pipeline...")
    run_ingestion()
    
    # Default test query if run directly
    sample_query = "What are the core components of the corrective self reflective RAG repository?"
    answer = run_crag_pipeline(sample_query)
    
    print("\n================ FINAL ANSWER ================\n")
    print(answer)
