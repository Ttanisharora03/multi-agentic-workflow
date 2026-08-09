import json
import time
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from src.main import app

print("Starting request to Dubai AI Travel Planner API...")
client = TestClient(app)

request_data = {
    "query": "Plan a 5 day trip to Dubai. Budget is $3000. I love: Adventure, Food, Culture. Additional requirements: I want to visit the Burj Khalifa on day 1, need a vegetarian diet...",
    "traveler_count": 1
}

start_time = time.time()
try:
    response = client.post("/api/v1/plan", json=request_data, timeout=300)
    print(f"Request completed in {time.time() - start_time:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    
    with open("response.json", "w") as f:
        json.dump(response.json(), f, indent=2)
        
    print("Response saved to response.json")
except Exception as e:
    print(f"Request failed: {e}")
