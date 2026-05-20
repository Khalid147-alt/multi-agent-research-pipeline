from crewai import Task


def build_tasks(researcher, analyst, fact_checker, writer, topic: str):
    research_task = Task(
        description=f"""Research: "{topic}"
        1. Run 3-5 search queries covering different angles
        2. Scrape top 3 results for full content
        3. Compile findings with full source URLs
        Output: Facts, quotes, statistics with sources (8+ sources minimum).""",
        expected_output="Structured research findings with 8+ cited sources",
        agent=researcher,
    )

    analysis_task = Task(
        description=f"""Analyze research on: "{topic}"
        1. Group into 3-5 subtopics
        2. List supporting evidence and contradictions per subtopic
        3. Note source agreement vs disagreement
        4. Identify 15-25 most important specific claims
        Output: Structured analysis per subtopic with evidence assessment.""",
        expected_output="Structured analysis with subtopics and evidence weight",
        agent=analyst,
        context=[research_task],
    )

    fact_check_task = Task(
        description="""Fact-check every claim from the analysis.
        Confidence scoring:
        - 90%+: 3+ sources agree
        - 70%: 2 sources agree
        - 50%: 1 source only
        - Below 50%: contradicted or single weak source
        Flag anything below 60% as UNVERIFIED.
        Output: JSON array [{claim, confidence_score, sources_count, flagged, reason}]""",
        expected_output="JSON array of scored and flagged claims",
        agent=fact_checker,
        context=[analysis_task],
    )

    write_task = Task(
        description=f"""Write final research report on: "{topic}"
        Structure:
        1. Executive Summary (3-4 sentences)
        2. 3-5 titled sections with inline citations [Source: URL]
           Each section ends with: Confidence: X%
        3. Flagged Claims Appendix (claims below 60%)
        4. Sources list
        Also generate HTML version for PDF export.""",
        expected_output="Full research report in markdown + HTML version",
        agent=writer,
        context=[fact_check_task],
    )

    return [research_task, analysis_task, fact_check_task, write_task]
