import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    default_model: str = "groq/llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./travel_planner.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()
