# Edge Cases & Failure Modes

This document outlines the known edge cases, constraints, and potential failure modes for the Dubai AI Travel Planner, as well as how the system mitigates them.

## 1. User Input Edge Cases

### 1.1 Impossible Constraints
* **Scenario:** The user requests a trip with an unrealistic budget (e.g., $100 for a 5-day trip for 2 people) or impossible scheduling (e.g., visiting 10 landmarks in 1 day).
* **Current Mitigation:** The system relies on the **Review Agent** to flag unrealistic itineraries. However, if the LLM cannot find *any* combination to satisfy the constraints, it may hallucinate cheap accommodations or fail validation. 
* **Future Enhancement:** Add a validation step in the `ParseRequest` node to immediately reject or warn users about mathematically impossible constraints before executing the expensive graph.

### 1.2 Contradictory Preferences
* **Scenario:** The user says "I want to be in the center of the city" but also "I want a quiet, secluded, and cheap place" or "Must see Burj Khalifa but avoid crowds completely".
* **Current Mitigation:** The LLM agents attempt to balance the requirements, often prioritizing explicit mentions over implicit ones.
* **Future Enhancement:** The orchestrator should prompt the user for clarification when heavily conflicting constraints are detected.

### 1.3 Ambiguous or Missing Information
* **Scenario:** User provides very little info: "Plan a trip to Dubai."
* **Current Mitigation:** The `ParseRequest` agent extracts defaults (e.g., 1 traveler, standard budget).
* **Future Enhancement:** Implement an interactive mode where the agent responds with clarifying questions if critical info (duration, rough budget) is missing.

## 2. LLM / Agent Edge Cases

### 2.1 Hallucinated Entities & Pricing
* **Scenario:** The LLM recommends a restaurant that is permanently closed, or estimates the cost of a luxury hotel at $50/night.
* **Current Mitigation:** The system uses zero-shot generation based on internal knowledge. The **Review Agent** evaluates realistic pricing based on generic knowledge but cannot verify live data.
* **Future Enhancement:** Integrate Phase 6 tools (Tavily/SerpAPI) to fetch live pricing and verify business operating hours.

### 2.2 Schema Validation Failures (Structured Output)
* **Scenario:** The LLM returns a markdown block instead of strict JSON, or forgets a required field (e.g., misses `budget_breakdown`).
* **Current Mitigation:** We use strict Pydantic schemas. LangChain/FastAPI handles basic retry loops on validation errors natively if configured.
* **Future Enhancement:** Leverage OpenAI/Gemini strict JSON mode and ensure robust `try/except` fallback logic in each node wrapper.

## 3. Pipeline / System Edge Cases

### 3.1 Review Loop Exhaustion (Infinite Loops)
* **Scenario:** The generated itinerary is consistently rejected by the Review Agent (e.g., budget is always exceeded), causing an infinite loop.
* **Current Mitigation:** The Graph Builder uses a state-managed `retry_count`. Once the limit (max 2 retries) is hit, the graph forces a `finalize` transition and returns the best effort itinerary with a `partial` status.

### 3.2 API Timeouts and Rate Limits
* **Scenario:** Groq or Gemini endpoints timeout, or we hit a rate limit (429 Too Many Requests).
* **Current Mitigation:** The `main.py` FastAPI app has a global `TimeoutError` handler returning a `504` response.
* **Future Enhancement:** Implement exponential backoff in the LLM call wrappers (using libraries like `tenacity`).

### 3.3 State Size Limits
* **Scenario:** Over multiple retries, the `PlannerState` dictionary becomes too large, potentially causing issues with database persistence (if added in the future).
* **Current Mitigation:** The current graph only tracks a lightweight state (mostly `str` and `dict`). Errors are appended, but limited to the retry loop constraints.
