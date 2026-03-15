from pydantic import BaseModel, Field

class RelevanceEvaluation(BaseModel):
    """Evaluation schema for assessing the relevance of retrieved context against a user query."""
    is_relevant: bool = Field(description="True if the retrieved context is relevant to the user query, False otherwise.")
    reasoning: str = Field(description="Brief reasoning for why the context is or isn't relevant.")

class GroundingEvaluation(BaseModel):
    """Evaluation schema for assessing how well a generated answer is grounded in the provided context."""
    score: float = Field(description="A score from 0.0 to 1.0 indicating how well the response is grounded in the context.")
    reasoning: str = Field(description="Brief reasoning justifying the assigned grounding score.")
