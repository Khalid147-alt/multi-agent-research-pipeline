from crewai import Agent

from agents.llms import get_researcher_llm
from tools.scraper_tool import ScraperTool
from tools.search_tool import TavilySearchTool


def build_researcher() -> Agent:
    return Agent(
        role="Senior Research Analyst",
        goal=(
            "Find 8-12 high-quality diverse sources on the topic. "
            "Extract key facts, statistics, expert opinions with full citations."
        ),
        backstory=(
            "You are a senior research analyst with 15 years experience. "
            "You never make up information. You always cite sources. "
            "You search multiple angles of every topic."
        ),
        tools=[TavilySearchTool(), ScraperTool()],
        llm=get_researcher_llm(),
        verbose=True,
        max_iter=5,
    )
