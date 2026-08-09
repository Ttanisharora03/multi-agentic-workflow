# Automations & Multi-Agent Systems — Problem Statement 

## Background
Planning a trip sounds simple at first, but in practice it quickly becomes overwhelming.

A traveler may have a request like:
*"Plan a 5-day trip to Dubai. $3,000 budget. Love food and architecture, hate crowds."*

To fulfill that well, we need to combine many different kinds of work:
- Understanding the traveler’s goals
- Researching destinations and attractions
- Comparing hotels and transport options
- Staying within budget
- Checking whether the final itinerary actually matches the request

## Objective
Design a simple Travel Planning Multi-Agent System that can automatically turn a short travel request into a useful trip plan.
The goal is not to build a perfect travel product, but to show how multiple specialized AI agents can work together on a real-world problem that product managers can easily understand.

## Real-World Problem to Solve
**"AI Travel Planner"**

A user gives a natural-language travel request such as:
*Plan a 5-day trip to Dubai. $3,000 budget. Love food and architecture, hate crowds.*

The system should produce:
- A day-by-day trip outline
- Suggested neighborhoods / areas to stay
- Travel logistics within the city
- Budget-friendly recommendations
- A final itinerary that respects the user’s preferences and constraints

## Multi-Agent System Design

### 1. Orchestrator Agent
**Role**: Creates the master plan, assigns work, and combines outputs into the final itinerary.
- **What it does**:
  - Reads the user request
  - Extracts key constraints:
    - Destination: Dubai
    - Duration: 5 days
    - Budget: $3,000
    - Preferences: food, architecture
    - Avoidances: crowds
  - Delegates tasks to the other agents
  - Synthesizes the final travel plan

### 2. Destination Research Agent
**Role**: Finds the best places, experiences, and food ideas based on the traveler’s preferences.
- **Possible inputs**:
  - Web search
  - Travel guides
  - Restaurant reviews
  - Attraction summaries
- **What it does**:
  - Recommends neighborhoods, architectural marvels, food districts, and local experiences
  - Suggests less-crowded options where possible
  - Identifies “must-do” vs “nice-to-have” items
- **Example output**:
  - Best times to visit the Burj Khalifa to avoid crowds
  - Food neighborhoods in Deira or Downtown Dubai
  - Off-peak or less-crowded experiences (e.g., morning desert safaris)

### 3. Logistics Agent
**Role**: Handles the practical side of moving and staying.
- **Possible inputs**:
  - Hotel APIs or sample hotel data
  - Metro routes / transit info
  - Maps / distance tools
- **What it does**:
  - Suggests where to stay in the city
  - Estimates travel time between locations
  - Recommends how to move around (e.g., Dubai Metro, taxis)
  - Builds a realistic sequence for each day
- **Example output**:
  - 3 nights in Downtown Dubai, 2 nights in Palm Jumeirah
  - Using the Metro vs. taking a taxi between locations
  - Day plans that reduce backtracking

### 4. Budget Agent
**Role**: Ensures the plan stays within budget.
- **Possible inputs**:
  - Currency conversion (USD to AED)
  - Estimated hotel costs
  - Food and transport price ranges
  - Attraction pricing
- **What it does**:
  - Breaks the budget into categories:
    - Stay
    - Transport
    - Food
    - Activities
  - Flags when the plan becomes too expensive
  - Suggests cheaper alternatives
- **Example output**:
  - Estimated total spend: $2,650
  - Hotel cost too high in Downtown Dubai → suggest alternate area like Business Bay or Al Barsha

### 5. Review Agent
**Role**: Validates the final itinerary before it is shown to the user.
- **What it checks**:
  - Does the itinerary fit into 5 days?
  - Does it focus on Dubai?
  - Is it within the $3,000 budget?
  - Does it align with “food + architecture”?
  - Does it try to avoid crowded experiences?
  - Is the plan realistic from a travel-time perspective?
- **This agent acts like a quality checker before the result is delivered.**

---
**Flow:**
`Orchestrator -> [Destination, Logistics, Budget in parallel] -> Review`
