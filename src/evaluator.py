from loguru import logger
from opik import track
from google import genai
from google.genai import types

from .schema import RelevanceEvaluation

# Reuse GenAI client
genai_client = genai.Client()

@track
def evaluate_relevance(query: str, context_chunks: list[dict]) -> RelevanceEvaluation:
    """
    Evaluates whether the retrieved context chunks contain information relevant
    to answering the user's query.
    """
    logger.info("Evaluating context relevance using CRAG logic...")
    
    # Combine chunks into a readable context
    context_text = "\n\n".join(
        [f"Source: {c['source']}\nText: {c['text']}" for c in context_chunks]
    )
    
    prompt = f"""
    You are a Fact-Checker for a Retrieval-Augmented Generation (RAG) system.
    Your task is to evaluate whether the provided context contains sufficient, relevant
    information to answer the user's query.
    
    Query: {query}
    
    Context Context:
    {context_text}
    
    If the context contains relevant information that can directly help answer the query, mark it as relevant.
    If the context is unrelated or the information is not helpful, mark it as irrelevant.
    """
    
    logger.info("Calling Gemini model to evaluate relevance...")
    response = genai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RelevanceEvaluation,
            temperature=0.0
        ),
    )
    
    # The output should natively parse back into schema
    result_text = response.text
    try:
        eval_result = RelevanceEvaluation.model_validate_json(result_text)
        logger.info(f"CRAG Result: is_relevant={eval_result.is_relevant} | Reasoning: {eval_result.reasoning}")
        return eval_result
    except Exception as e:
        logger.error(f"Failed to parse RelevanceEvaluation JSON: {e}")
        # Default to False (fallback to web) if there's a parsing error
        return RelevanceEvaluation(is_relevant=False, reasoning=f"Parse Error: {e}")
