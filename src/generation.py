from loguru import logger
from opik import track
from google import genai
from google.genai import types

from .schema import GroundingEvaluation

genai_client = genai.Client()

@track
def generate_draft(query: str, context_chunks: list[dict], feedback: str = None) -> str:
    """Generates an answer based ONLY on the provided context chunks."""
    logger.info("Generating draft answer...")
    
    context_text = "\n\n".join(
        [f"Source: {c['source']}\nText: {c['text']}" for c in context_chunks]
    )
    
    prompt = f"""
    You are an expert technical assistant.
    Answer the user's query using ONLY the provided context. If the context does not contain the answer, say so.
    
    Query: {query}
    
    Context:
    {context_text}
    """
    
    if feedback:
        logger.warning(f"Previous draft was criticized: {feedback}")
        prompt += f"\n\nRefine your previous answer based on the critic's feedback:\n{feedback}"
    
    response = genai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    
    return response.text

@track
def critique_generation(query: str, context_chunks: list[dict], answer: str) -> GroundingEvaluation:
    """Evaluates the generation for grounding/hallucination against the context."""
    logger.info("Evaluating grounding of the drafted answer...")
    
    context_text = "\n\n".join(
        [f"Source: {c['source']}\nText: {c['text']}" for c in context_chunks]
    )
    
    prompt = f"""
    You are a Self-Reflective Critic for a RAG system.
    Evaluate the provided generated answer against the context provided.
    
    1. Grounding Score: How well the answer is supported by the context? 
       - 0.0 (completely hallucinated) to 1.0 (perfectly grounded).
    
    2. Utility: Does the answer actually address the user's intent?
       - CRITICAL: Set 'utility' to False if the answer is a disclaimer like "I don't know", "The context doesn't say", "Information missing", or if it fails to answer any substantial part of the query.
       - Set 'utility' to True ONLY if the answer provides the actual information the user is looking for.
       - A "grounded" disclaimer is still 'utility=False'.
    
    Query: {query}
    
    Context:
    {context_text}
    
    Generated Answer:
    {answer}
    """
    
    response = genai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GroundingEvaluation,
            temperature=0.0
        ),
    )
    
    try:
        eval_result = GroundingEvaluation.model_validate_json(response.text)
        logger.info(f"Critique Grounding Score: {eval_result.score} | Reasoning: {eval_result.reasoning}")
        return eval_result
    except Exception as e:
        logger.error(f"Failed to parse GroundingEvaluation JSON: {e}")
        # Default to a passing score if parsing fails to avoid infinite loops, but warn heavily
        return GroundingEvaluation(score=1.0, reasoning=f"Parse Error on Critique: {e}")

@track
def iterative_generation(query: str, context_chunks: list[dict], max_iterations: int = 3) -> tuple[str, str]:
    """
    Iterates generation and critique. 
    Returns: (final_answer, retry_feedback_if_failed_fully)
    """
    feedback = None
    final_draft = ""
    
    for i in range(max_iterations):
        logger.info(f"--- Iteration {i+1}/{max_iterations} ---")
        final_draft = generate_draft(query, context_chunks, feedback)
        
        eval_result = critique_generation(query, context_chunks, final_draft)
        
        if eval_result.score >= 0.8 and eval_result.utility:
            logger.info("Generation passed critique and is useful. Returning final answer.")
            return final_draft, None
        elif eval_result.score >= 0.4 and eval_result.utility:
            logger.warning(f"Generation partially grounded (Score: {eval_result.score}). Attempting refinement...")
            feedback = eval_result.reasoning
        elif not eval_result.utility:
            logger.error(f"Generation lacks UTILITY (Score: {eval_result.score}). Forcefully signalling re-retrieval.")
            # If the answer is grounded but useless (e.g., "I don't know"), we must seek better data.
            return final_draft, f"Insufficient information in current context. Reason: {eval_result.reasoning}"
        else:
            logger.error(f"Generation POORLY grounded (Score: {eval_result.score}). Signalling for re-retrieval reset.")
            # Return reasoning as feedback to main.py for a potential query rewrite/re-retrieval
            return final_draft, eval_result.reasoning
            
    logger.warning("Reached max iterations in SR-RAG refinement loop.")
    return final_draft, (feedback or "Max iterations reached without high grounding and utility.")

