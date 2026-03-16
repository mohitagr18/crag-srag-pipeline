from pydantic import BaseModel, Field

from typing import Literal

class RelevanceEvaluation(BaseModel):
    """Evaluation schema for assessing the relevance of retrieved context against a user query."""
    status: Literal["correct", "ambiguous", "incorrect"] = Field(
        description="Classification of context relevance: 'correct' (sufficient), 'ambiguous' (partially relevant, needs more), 'incorrect' (irrelevant)."
    )
    reasoning: str = Field(description="Brief reasoning for why the context was classified as such.")

class GroundingEvaluation(BaseModel):
    """Evaluation schema for assessing how well a generated answer is grounded and helpful."""
    score: float = Field(description="A score from 0.0 to 1.0 indicating how well the response is grounded in the context.")
    utility: bool = Field(description="True if the response actually answers the user's question. False if it is a disclaimer like 'I don't know' or is otherwise unhelpful.")
    reasoning: str = Field(description="Brief reasoning justifying the assigned score and utility.")
