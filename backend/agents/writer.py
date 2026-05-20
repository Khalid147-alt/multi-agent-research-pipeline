from crewai import Agent

from agents.llms import get_gemini_llm
from tools.pdf_tool import PDFGeneratorTool


def build_writer() -> Agent:
    return Agent(
        role="Technical Writer",
        goal=(
            "Produce a strict-markdown research report: ## Executive Summary, "
            "3-5 ## sections each ending with `Confidence: NN%`, optional "
            "## Flagged Claims, and a final ## Sources numbered URL list. "
            "Plain markdown only — never emit HTML tags or code fences."
        ),
        backstory=(
            "Senior technical writer for business audiences. Writes plain markdown "
            "with `##` headings, inline `[1]` citations, and explicit per-section "
            "confidence scores. Never wraps output in HTML or code blocks."
        ),
        tools=[PDFGeneratorTool()],
        llm=get_gemini_llm(),
        verbose=True,
    )
