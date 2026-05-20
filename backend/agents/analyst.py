from crewai import Agent

from agents.llms import get_gemini_llm


def build_analyst() -> Agent:
    return Agent(
        role="Critical Data Analyst",
        goal=(
            "Cross-reference research findings. Identify agreements and conflicts. "
            "Produce structured analysis with subtopics and evidence weight per claim."
        ),
        backstory=(
            "You specialize in cross-referencing multiple sources and "
            "identifying when sources agree, conflict, and what evidence supports."
        ),
        llm=get_gemini_llm(),
        verbose=True,
    )
