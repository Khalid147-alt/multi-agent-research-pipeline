from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str = ""
    groq_api_key: str = ""
    tavily_api_key: str = ""
    database_url: str = "postgresql://admin:password@localhost:5432/research_pipeline"
    redis_url: str = "redis://localhost:6379"
    environment: str = "development"
    use_sqlite: bool = False
    max_search_results: int = 8
    gemini_model: str = "gemini-2.5-flash-lite"
    groq_model: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
