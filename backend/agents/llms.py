from functools import lru_cache

from crewai import LLM

from config import get_settings


@lru_cache(maxsize=1)
def get_gemini_llm() -> LLM:
    """Analyst, Fact Checker, Writer — deep reasoning. Temperature 0.3."""
    s = get_settings()
    return LLM(
        model=f"gemini/{s.gemini_model}",
        api_key=s.gemini_api_key,
        temperature=0.3,
    )


@lru_cache(maxsize=1)
def get_researcher_llm() -> LLM:
    """Researcher — wants more breadth, lower temperature to stay factual."""
    s = get_settings()
    return LLM(
        model=f"gemini/{s.gemini_model}",
        api_key=s.gemini_api_key,
        temperature=0.1,
    )
