from pydantic import BaseModel, Field

from typing import Literal

class RelevanceEvaluation(BaseModel):
    """Evaluation schema for assessing the relevance of retrieved context against a user query."""
    status: Literal["correct", "ambiguous", "incorrect"] = Field(
        description="Classification of context relevance: 'correct' (sufficient), 'ambiguous' (partially relevant, needs more), 'incorrect' (irrelevant)."
    )
    reasoning: str = Field(description="Brief reasoning for why the context was classified as such.")

class GroundingEvaluation(BaseModel):
    """Evaluation schema for assessing how well a generated answer is grounded in the provided context."""
    score: float = Field(description="A score from 0.0 to 1.0 indicating how well the response is grounded in the context.")
    reasoning: str = Field(description="Brief reasoning justifying the assigned grounding score.")
