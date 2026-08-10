# Architecture — Dubai AI Travel Planner (Multi-Agent System)

> **Reference**: [problemstatement.md](file:///c:/Users/tanis/projects/Multi%20agentic%20next%20leap/docs/problemstatement.md)
> **Scope**: Dubai only (v1)

---

## 1. High-Level Overview

The system accepts a natural-language travel request (e.g., *"Plan a 5-day trip to Dubai. $3,000 budget. Love food and architecture, hate crowds."*) and produces a validated, day-by-day itinerary through the coordinated work of five specialized AI agents.

```mermaid
flowchart LR
    U[User] -->|Natural language request| API[FastAPI Gateway]
    API --> O[Orchestrator Agent]
    O -->|Parallel fan-out| D[Destination Research Agent]
    O -->|Parallel fan-out| L[Logistics Agent]
    O -->|Parallel fan-out| B[Budget Agent]
    D --> O
    L --> O
    B --> O
    O -->|Draft itinerary| R[Review Agent]
    R -->|Validated itinerary| O
    O -->|Final plan| API
    API -->|JSON response| U
```

---

## 2. Technology Stack

| Layer            | Technology                   | Rationale                                                                 |
|------------------|------------------------------|---------------------------------------------------------------------------|
| Language         | **Python 3.12+**             | Strongest LLM ecosystem, async-first with `asyncio`                       |
| Agent Framework  | **LangGraph**                | Graph-based orchestration with native support for parallel fan-out/fan-in |
| LLM Provider     | **GROQ** (primary) & **Gemini** | GROQ for fast multi-agent reasoning, Gemini for complex review validation |
| LLM Fallback     | **OpenAI GPT-4o**            | Fallback for reliability; swappable via LiteLLM                           |
| LLM Gateway      | **LiteLLM**                  | Unified interface across providers; handles retries, rate-limits, caching |
| Web Framework    | **FastAPI**                  | Async API layer, auto-generated OpenAPI docs, streaming support           |
| Data Validation  | **Pydantic v2**              | Typed schemas for all agent I/O, request/response validation              |
| Database         | **PostgreSQL + SQLAlchemy**  | Persistent trip storage, user history, agent execution logs               |
| Caching          | **Redis**                    | LLM response caching, rate-limiting, session state                        |
| Task Queue       | **Celery** (optional v2)     | Background processing for long-running plans                              |
| Testing          | **pytest + pytest-asyncio**  | Unit + integration test suite                                             |
| Containerization | **Docker + Docker Compose**  | Consistent dev/prod environments                                          |
| CI/CD            | **GitHub Actions**           | Automated lint, test, build, deploy pipeline                              |

---

## 3. Agent Architecture (Deep Dive)

### 3.1 Orchestrator Agent

The brain of the system. It owns the entire lifecycle of a travel planning request.

**Responsibilities:**
1. **Parse** the user's natural-language request via an LLM call with structured output (Pydantic model).
2. **Validate** extracted constraints (destination = Dubai, duration, budget, preferences, avoidances).
3. **Dispatch** tasks to Destination, Logistics, and Budget agents **in parallel** using LangGraph's fan-out.
4. **Merge** results from all three agents into a draft itinerary.
5. **Hand off** the draft to the Review Agent.
6. **Handle feedback loops** — if the Review Agent rejects the plan, the Orchestrator adjusts and re-dispatches (max 2 retries).
7. **Return** the final validated itinerary.

**Parsed Request Schema:**
```python
class TravelRequest(BaseModel):
    destination: str             # "Dubai"
    duration_days: int           # 5
    budget_usd: float            # 3000.0
    preferences: list[str]       # ["food", "architecture"]
    avoidances: list[str]        # ["crowds"]
    traveler_count: int = 1
    raw_input: str               # Original user text
```

**State Graph (LangGraph):**
```mermaid
stateDiagram-v2
    [*] --> ParseRequest
    ParseRequest --> ValidateConstraints
    ValidateConstraints --> FanOut
    
    state FanOut <<fork>>
    FanOut --> DestinationResearch
    FanOut --> LogisticsPlanning
    FanOut --> BudgetAnalysis
    
    state FanIn <<join>>
    DestinationResearch --> FanIn
    LogisticsPlanning --> FanIn
    BudgetAnalysis --> FanIn
    
    FanIn --> MergeDraft
    MergeDraft --> ReviewValidation
    ReviewValidation --> RetryDecision
    
    RetryDecision --> FanOut : rejected & retries < 2
    RetryDecision --> FinalOutput : approved
    
    FinalOutput --> [*]
```

---

### 3.2 Destination Research Agent

**Input:** `TravelRequest` (destination, preferences, avoidances)

**Process:**
1. Query the LLM with a Dubai-specific system prompt that includes knowledge of Dubai's neighborhoods, landmarks, food districts, and cultural attractions.
2. Optionally augment via web search tool (SerpAPI / Tavily) for real-time data (opening hours, seasonal events).
3. Categorize results into `must-do`, `nice-to-have`, and `skip` (based on avoidances).
4. Tag each recommendation with a crowd-level estimate and best visit time.

**Output Schema:**
```python
class Recommendation(BaseModel):
    name: str                          # "Al Fahidi Historical Neighbourhood"
    category: Literal["landmark", "food", "experience", "culture"]
    neighborhood: str                  # "Bur Dubai"
    estimated_duration_hours: float    # 2.0
    crowd_level: Literal["low", "medium", "high"]
    best_time_to_visit: str            # "Early morning (before 9 AM)"
    estimated_cost_usd: float          # 0.0 (free)
    priority: Literal["must-do", "nice-to-have"]
    description: str

class DestinationOutput(BaseModel):
    recommendations: list[Recommendation]
    neighborhoods_summary: dict[str, str]   # { "Deira": "Traditional markets, spice souk..." }
```

---

### 3.3 Logistics Agent

**Input:** `TravelRequest` + `DestinationOutput` (from shared state)

**Process:**
1. Select accommodation areas based on preferences and budget range.
2. Map out daily routes that minimize travel time and backtracking.
3. Recommend transport modes (Dubai Metro, taxis/ride-hail, water taxis, walking).
4. Build a day-by-day schedule skeleton with time blocks.

**Output Schema:**
```python
class Accommodation(BaseModel):
    area: str                        # "Business Bay"
    hotel_tier: Literal["budget", "mid-range", "luxury"]
    estimated_nightly_cost_usd: float
    nights: int
    rationale: str

class DaySchedule(BaseModel):
    day: int                         # 1
    theme: str                       # "Old Dubai & Spice Markets"
    activities: list[str]            # ["Al Fahidi Neighbourhood", "Spice Souk", ...]
    transport_modes: list[str]       # ["Metro", "Walking", "Taxi"]
    estimated_travel_time_mins: int  # 45
    notes: str

class LogisticsOutput(BaseModel):
    accommodations: list[Accommodation]
    daily_schedule: list[DaySchedule]
    transport_tips: list[str]
```

---

### 3.4 Budget Agent

**Input:** `TravelRequest` + `DestinationOutput` + `LogisticsOutput`

**Process:**
1. Pull estimated costs from Destination and Logistics outputs.
2. Cross-reference costs with real data sourced from [Wikivoyage Dubai Budget](https://en.wikivoyage.org/wiki/Dubai#Budget).
3. Convert and normalize to USD (1 USD ≈ 3.67 AED).
4. Categorize spending into: Stay, Transport, Food, Activities, Miscellaneous.
5. Compare total against the user's budget.
5. If over budget → flag specific items and suggest cheaper alternatives.

**Output Schema:**
```python
class BudgetBreakdown(BaseModel):
    category: str                     # "Stay"
    estimated_cost_usd: float         # 850.0
    percentage_of_budget: float       # 28.3

class BudgetAlert(BaseModel):
    severity: Literal["info", "warning", "over-budget"]
    message: str                      # "Hotel cost in Downtown too high"
    suggestion: str                   # "Consider Business Bay — saves ~$200"

class BudgetOutput(BaseModel):
    total_estimated_usd: float
    budget_limit_usd: float
    remaining_usd: float
    breakdown: list[BudgetBreakdown]
    alerts: list[BudgetAlert]
    is_within_budget: bool
```

---

### 3.5 Review Agent

**Input:** Full draft itinerary (merged Destination + Logistics + Budget outputs)

**Validation Checklist:**
| # | Check                                      | Action on Failure                          |
|---|--------------------------------------------|--------------------------------------------|
| 1 | Itinerary fits within requested duration   | Flag excess days, suggest condensing       |
| 2 | Destination is Dubai                       | Reject if off-destination items included   |
| 3 | Total cost ≤ budget                        | Return budget alerts for Orchestrator      |
| 4 | Preferences are addressed                  | Flag missing preference coverage           |
| 5 | Avoidances are respected                   | Flag high-crowd items without alternatives |
| 6 | Travel times are realistic                 | Flag unrealistic day plans                 |

**Output Schema:**
```python
class ReviewResult(BaseModel):
    approved: bool
    overall_score: float              # 0.0 to 1.0
    issues: list[str]                 # ["Day 3 has 6 hours of travel — too packed"]
    suggestions: list[str]            # ["Swap afternoon activity to something nearby"]
    verdict: str                      # "Approved with minor suggestions"
```

---

## 4. Data Flow & Agent Communication

All agents communicate through a **shared state object** managed by LangGraph. No direct agent-to-agent calls.

```mermaid
flowchart TB
    subgraph SharedState["LangGraph Shared State"]
        TR[TravelRequest]
        DO[DestinationOutput]
        LO[LogisticsOutput]
        BO[BudgetOutput]
        DI[DraftItinerary]
        RR[ReviewResult]
        FI[FinalItinerary]
    end

    OA[Orchestrator] -->|writes| TR
    DRA[Destination Agent] -->|reads| TR
    DRA -->|writes| DO
    LA[Logistics Agent] -->|reads| TR
    LA -->|reads| DO
    LA -->|writes| LO
    BA[Budget Agent] -->|reads| TR
    BA -->|reads| DO
    BA -->|reads| LO
    BA -->|writes| BO
    OA -->|reads all, writes| DI
    RA[Review Agent] -->|reads| DI
    RA -->|writes| RR
    OA -->|reads RR, writes| FI
```

> **Note on parallelism:** Destination, Logistics, and Budget agents are dispatched in parallel. However, the Budget Agent internally depends on outputs from Destination and Logistics. LangGraph handles this by allowing the Budget Agent's node to read from the shared state — if Destination or Logistics data isn't yet available, LangGraph's graph edges enforce the correct execution order.

**Refined execution order:**
```
Orchestrator (parse)
    ├── Destination Agent  ──┐
    │                        ├── Budget Agent
    └── Logistics Agent   ──┘        │
                                     ▼
                            Orchestrator (merge)
                                     │
                              Review Agent
                                     │
                            Orchestrator (finalize)
```

---

## 5. API Design

### 5.1 REST Endpoints

| Method | Endpoint               | Description                        |
|--------|------------------------|------------------------------------|
| POST   | `/api/v1/plan`         | Submit a new travel planning request |
| GET    | `/api/v1/plan/{id}`    | Get a plan by ID                   |
| GET    | `/api/v1/plan/{id}/status` | Check planning status (for async) |
| POST   | `/api/v1/plan/{id}/feedback` | User feedback on a plan        |
| GET    | `/api/v1/health`       | Health check                       |

### 5.2 Request / Response Examples

**POST `/api/v1/plan`**

Request:
```json
{
  "query": "Plan a 5-day trip to Dubai. $3,000 budget. Love food and architecture, hate crowds.",
  "traveler_count": 1
}
```

Response (202 Accepted for async, or 200 with full plan for sync):
```json
{
  "plan_id": "pln_a1b2c3d4",
  "status": "completed",
  "itinerary": {
    "destination": "Dubai",
    "duration_days": 5,
    "total_estimated_cost_usd": 2650.00,
    "budget_limit_usd": 3000.00,
    "days": [
      {
        "day": 1,
        "theme": "Arrival & Old Dubai",
        "activities": [
          {
            "name": "Check in at Rove Downtown Hotel",
            "time": "14:00",
            "category": "logistics",
            "cost_usd": 0
          },
          {
            "name": "Al Fahidi Historical Neighbourhood",
            "time": "16:00",
            "category": "culture",
            "cost_usd": 0,
            "crowd_level": "low"
          },
          {
            "name": "Dinner at Arabian Tea House",
            "time": "19:00",
            "category": "food",
            "cost_usd": 25
          }
        ],
        "transport": ["Taxi from airport", "Walking"],
        "day_cost_usd": 195
      }
    ],
    "accommodations": [...],
    "budget_breakdown": {...},
    "review": {
      "approved": true,
      "score": 0.92,
      "verdict": "Plan is well-balanced and within budget."
    }
  }
}
```

---

## 6. Project Structure

```
Multi agentic next leap/
├── docs/
│   ├── problemstatement.md
│   ├── architecture.md              ← You are here
│   └── problemstatement.txt
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Settings via pydantic-settings
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Orchestrator Agent
│   │   ├── destination.py           # Destination Research Agent
│   │   ├── logistics.py             # Logistics Agent
│   │   ├── budget.py                # Budget Agent
│   │   └── review.py                # Review Agent
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                 # Shared state definition (TypedDict)
│   │   ├── nodes.py                 # LangGraph node functions
│   │   └── builder.py              # Graph construction & compilation
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── request.py               # TravelRequest, API request models
│   │   ├── response.py              # API response models
│   │   ├── destination.py           # DestinationOutput, Recommendation
│   │   ├── logistics.py             # LogisticsOutput, DaySchedule
│   │   ├── budget.py                # BudgetOutput, BudgetBreakdown
│   │   └── review.py                # ReviewResult
│   ├── prompts/
│   │   ├── orchestrator.txt         # System prompt for Orchestrator
│   │   ├── destination.txt          # System prompt for Destination Agent
│   │   ├── logistics.txt            # System prompt for Logistics Agent
│   │   ├── budget.txt               # System prompt for Budget Agent
│   │   └── review.txt               # System prompt for Review Agent
│   ├── tools/                       # External tool integrations
│   │   ├── __init__.py
│   │   ├── search.py                # Web search (SerpAPI / Tavily)
│   │   └── currency.py              # Currency conversion utility
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                # API route definitions
│   │   └── dependencies.py          # FastAPI dependency injection
│   └── db/
│       ├── __init__.py
│       ├── models.py                # SQLAlchemy ORM models
│       └── session.py               # DB session management
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── test_orchestrator.py
│   ├── test_destination.py
│   ├── test_logistics.py
│   ├── test_budget.py
│   ├── test_review.py
│   ├── test_graph.py                # End-to-end graph execution
│   └── test_api.py                  # API endpoint tests
├── .env.example                     # Environment variable template
├── .gitignore
├── pyproject.toml                   # Project metadata & dependencies
├── docker-compose.yml               # Local dev stack
├── Dockerfile
└── README.md
```

---

## 7. Configuration & Environment

All configuration is managed via **pydantic-settings** with `.env` file support.

```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    gemini_api_key: str
    openai_api_key: str = ""           # Optional fallback
    default_llm_provider: str = "gemini"
    default_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.3
    llm_max_retries: int = 2

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/travel_planner"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Tools
    serpapi_key: str = ""
    tavily_api_key: str = ""

    # Agent behavior
    max_review_retries: int = 2
    budget_currency: str = "USD"
    target_city: str = "Dubai"         # Hardcoded for v1

    class Config:
        env_file = ".env"
```

---

## 8. LLM Strategy

### Model Selection
| Agent               | Model                    | Rate Limits & Reasoning                                                 |
|----------------------|--------------------------|--------------------------------------------------------------------------|
| Orchestrator         | `groq/llama-3.3-70b-versatile` | Needs strong reasoning. Limits: 30 RPM, 1k RPD, 12k TPM, 100k TPD       |
| Destination Research | `groq/llama-3.3-70b-versatile` | Speed-optimized. Limits: 30 RPM, 1k RPD, 12k TPM, 100k TPD              |
| Logistics            | `groq/llama-3.3-70b-versatile` | Structured output focus. Limits: 30 RPM, 1k RPD, 12k TPM, 100k TPD      |
| Budget               | `groq/llama-3.3-70b-versatile` | Primarily arithmetic. Limits: 30 RPM, 1k RPD, 12k TPM, 100k TPD         |
| Review               | `gemini-2.5-flash`       | Fast validation. Limits: 5 RPM, 20 RPD, 250k TPM                        |

### Prompt Engineering
- Each agent has a dedicated system prompt stored in `src/prompts/`.
- All prompts include Dubai-specific context (neighborhoods, landmarks, transport system, approximate costs).
- Structured output is enforced using Pydantic models with `response_format` or function-calling schemas.
- Temperature is kept low (0.2–0.3) for consistency.

### Caching
- LLM responses are cached in Redis with a TTL of 24 hours.
- Cache key = `hash(agent_name + serialized_input)`.
- Cache can be bypassed per-request with a `?fresh=true` query param.

---

## 9. Error Handling & Resilience

```mermaid
flowchart TD
    A[Agent Call] --> B{LLM Response OK?}
    B -->|Yes| C[Parse Output]
    B -->|No| D{Retries Left?}
    D -->|Yes| E[Retry with Backoff]
    E --> A
    D -->|No| F{Fallback Provider?}
    F -->|Yes| G[Switch to OpenAI]
    G --> A
    F -->|No| H[Return Graceful Error]
    
    C --> I{Valid Schema?}
    I -->|Yes| J[Continue Pipeline]
    I -->|No| K[Re-prompt with Error Context]
    K --> A
```

**Key strategies:**
- **Retry with exponential backoff** — up to 3 retries per LLM call.
- **Provider fallback** — if Gemini fails, automatically switch to OpenAI via LiteLLM.
- **Schema re-prompting** — if the LLM returns malformed output, re-prompt with the Pydantic validation error message.
- **Timeout** — 60-second timeout per agent; 5-minute timeout for the full pipeline.
- **Graceful degradation** — if one parallel agent fails, the system can still produce a partial plan with a warning.

---

## 10. Observability & Logging

| Concern        | Tool                     | Details                                               |
|----------------|--------------------------|-------------------------------------------------------|
| Structured Logs| **structlog**            | JSON-formatted logs with correlation IDs per request   |
| LLM Tracing    | **LangSmith** (optional) | Full trace of LangGraph execution, prompt/response pairs |
| Metrics        | **Prometheus** (v2)      | Latency per agent, token usage, error rates            |
| Dashboards     | **Grafana** (v2)         | Visualization of metrics                               |

Each request gets a unique `plan_id` that is threaded through all logs for easy debugging.

---

## 11. Security Considerations

- **API keys** are stored in environment variables, never committed to source.
- **Input sanitization** — user input is sanitized before being injected into prompts to prevent prompt injection.
- **Rate limiting** — API endpoints are rate-limited via Redis (e.g., 10 requests/min per IP).
- **No PII storage** — v1 does not store user personal data; only the query and generated plan.

---

## 12. Deployment Strategy (v1)

```mermaid
flowchart LR
    subgraph Local Dev
        DC[Docker Compose]
        DC --> FA[FastAPI Container]
        DC --> PG[PostgreSQL Container]
        DC --> RD[Redis Container]
    end

    subgraph Production
        GCR[Cloud Run / Railway]
        GCR --> FA2[FastAPI App]
        FA2 --> PG2[Managed PostgreSQL]
        FA2 --> RD2[Managed Redis]
    end
```

**v1 target:** Deploy on **Railway** or **Google Cloud Run** for simplicity. Single service, no microservices split.

---

## 13. Development Phases

### Phase 1 — Core Pipeline (MVP)
- [ ] Project scaffolding (pyproject.toml, Docker, structure)
- [ ] Pydantic schemas for all agent I/O
- [ ] Orchestrator Agent with request parsing
- [ ] Destination Research Agent (LLM-only, no web search)
- [ ] Logistics Agent (LLM-only, static Dubai knowledge)
- [ ] Budget Agent (LLM-only, hardcoded cost ranges)
- [ ] Review Agent with validation checklist
- [ ] LangGraph wiring (fan-out → fan-in → review loop)
- [ ] FastAPI endpoint (`POST /api/v1/plan`)
- [ ] Basic tests

### Phase 2 — Enhancement
- [ ] Web search tool integration (SerpAPI / Tavily)
- [ ] Redis caching for LLM responses
- [ ] PostgreSQL for plan persistence
- [ ] Speech-to-Text API (Groq Whisper)
- [ ] Streaming response support (SSE)
- [ ] LangSmith tracing integration
- [ ] Expanded test coverage

### Phase 3 — Production Readiness
- [ ] Docker Compose for local dev
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Rate limiting & input validation hardening
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Deployment to Cloud Run / Railway

---

## 14. Key Design Decisions

| Decision                              | Choice                  | Why                                                                                           |
|---------------------------------------|-------------------------|-----------------------------------------------------------------------------------------------|
| Agent framework                       | LangGraph               | Native parallel execution, state management, retry loops — exactly what this flow needs       |
| LLM routing                           | LiteLLM                 | Swap providers without code changes; built-in retry logic                                     |
| Shared state vs. message passing      | Shared state (TypedDict)| Simpler mental model; all agents read/write to one state object managed by LangGraph          |
| Sync vs. Async API                    | Async (with sync option)| Plans can take 30–60s; async prevents blocking                                               |
| Dubai-only scope (v1)                 | Hardcoded               | Reduces prompt complexity; can generalize in v2 by making prompts template-driven             |
| Prompts as text files                 | `.txt` in `src/prompts/`| Easy to edit without touching Python code; version-controlled alongside codebase              |
