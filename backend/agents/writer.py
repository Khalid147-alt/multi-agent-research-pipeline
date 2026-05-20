from crewai import Agent

from agents.llms import get_gemini_llm
from tools.pdf_tool import PDFGeneratorTool


def build_writer() -> Agent:
    return Agent(
        role="Technical Writer",
        goal=(
            "Produce final research report: executive summary, 3-5 titled sections "
            "with inline citations [Source: URL], confidence % per section, "
            "flagged claims appendix. Also generate HTML version for PDF export."
        ),
        backstory=(
            "Senior technical writer for business audiences. "
            "Always cite sources inline. Label confidence clearly. Plain English."
        ),
        tools=[PDFGeneratorTool()],
        llm=get_gemini_llm(),
        verbose=True,
    )
