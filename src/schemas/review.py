from pydantic import BaseModel
from typing import Optional

class ReviewResult(BaseModel):
    approved: bool
    overall_score: float
    issues: list[str]
    suggestions: list[str]
    verdict: str
