from crewai import Agent

from agents.llms import get_gemini_llm


def build_fact_checker() -> Agent:
    return Agent(
        role="Fact Checker",
        goal=(
            "Assign confidence score (0-100%) to every claim. "
            "Flag claims below 60% as UNVERIFIED. "
            "Return JSON: [{claim, confidence_score, sources_count, flagged, reason}]"
        ),
        backstory=(
            "You are a meticulous fact-checker. You score based on source count, "
            "quality, and cross-source agreement. You flag anything uncertain."
        ),
        llm=get_gemini_llm(),
        verbose=True,
    )
