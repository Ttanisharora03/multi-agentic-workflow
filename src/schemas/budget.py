from pydantic import BaseModel
from typing import Optional

class BudgetAlert(BaseModel):
    severity: str
    message: str
    suggestion: str

class BudgetBreakdown(BaseModel):
    category: str
    estimated_cost_usd: float
    percentage_of_budget: float

class BudgetOutput(BaseModel):
    total_estimated_usd: float
    budget_limit_usd: float
    remaining_usd: float
    breakdown: list[BudgetBreakdown]
    alerts: list[BudgetAlert]
    is_within_budget: bool
