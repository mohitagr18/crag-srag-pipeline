from loguru import logger
from opik import track
from google import genai
from google.genai import types

genai_client = genai.Client()

@track
def rewrite_query(original_query: str, critic_feedback: str) -> str:
    """
    Rewrites the user's query into a more specific, search-optimized string
    based on the critic's feedback about missing or hallucinated information.
    """
    logger.info(f"Rewriting query based on feedback: {critic_feedback}")
    
    prompt = f"""
    You are a Query Transformation Agent. 
    The user asked: "{original_query}"
    
    A previous attempt to answer this using RAG failed or was ungrounded.
    Critic Feedback: "{critic_feedback}"
    
    Your task is to rewrite the original query into a single, high-fidelity search query 
    that specifically targets the missing information mentioned in the feedback.
    
    Return ONLY the new query string.
    """
    
    response = genai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0),
    )
    
    new_query = response.text.strip().replace('"', '')
    logger.info(f"New Refined Query: '{new_query}'")
    return new_query
