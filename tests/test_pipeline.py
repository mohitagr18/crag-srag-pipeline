import os
import pytest
from src.ingestion import run_ingestion
from src.retrieval import retrieve_qdrant, fallback_to_web
from src.evaluator import evaluate_relevance
from src.main import run_crag_pipeline

@pytest.fixture(scope="session", autouse=True)
def setup_qdrant():
    """Ensure the in-memory vector store is populated before any tests run."""
    run_ingestion()

def test_qdrant_retrieval_success():
    """
    Test that querying about the repo architecture successfully retrieves context
    from Qdrant and passes CRAG evaluation.
    """
    query = "What are the core components of the corrective self reflective RAG repository?"
    
    # Check retrieval hits
    chunks = retrieve_qdrant(query)
    assert len(chunks) > 0, "Expected Qdrant to return some chunks."
    
    # Check CRAG Evaluation
    eval_result = evaluate_relevance(query, chunks)
    assert eval_result.is_relevant is True, "Expected CRAG to mark these chunks as relevant."
    
    # Check end-to-end generation
    answer = run_crag_pipeline(query)
    assert len(answer) > 20, "Expected a substantial drafted answer."

def test_serper_web_fallback():
    """
    Test that a query unrelated to the repo fails CRAG and triggers the Serper web fallback.
    """
    query = "What are the latest developments in large language models today?"
    
    # Retrieve from Qdrant (which only has repo details)
    chunks = retrieve_qdrant(query)
    
    # CRAG Evaluation should FAIL because the repo docs don't cover current external events
    eval_result = evaluate_relevance(query, chunks)
    assert eval_result.is_relevant is False, "Expected CRAG to mark these chunks as irrelevant since Qdrant only knows about the repo."
    
    # Ensure fallback alone pulls web snippets
    web_chunks = fallback_to_web(query)
    assert len(web_chunks) > 0, "Expected Serper API to return fallback search results."
    
    # Ensure end-to-end pipeline still maps the fallback correctly and outputs an answer
    answer = run_crag_pipeline(query)
    assert len(answer) > 20, "Expected pipeline to answer using Serper fallback."
