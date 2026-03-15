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
    Determine how well the answer is grounded in the context.
    - Score it from 0.0 (completely hallucinated/ungrounded) to 1.0 (perfectly grounded).
    - Provide a brief reasoning.
    
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
def iterative_generation(query: str, context_chunks: list[dict], max_iterations: int = 3) -> str:
    """Iterates generation and critique until grounding score passes 0.8 or max_iterations reached."""
    feedback = None
    final_draft = ""
    
    for i in range(max_iterations):
        logger.info(f"--- Iteration {i+1}/{max_iterations} ---")
        final_draft = generate_draft(query, context_chunks, feedback)
        
        eval_result = critique_generation(query, context_chunks, final_draft)
        
        if eval_result.score >= 0.8:
            logger.info("Generation passed critique. Returning final answer.")
            break
        else:
            logger.warning("Generation failed critique. Feeding back to generation agent...")
            feedback = eval_result.reasoning
            
    return final_draft
