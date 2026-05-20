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
        description=f"""Write the final research report on: "{topic}"

OUTPUT FORMAT — STRICT. The report is parsed by a downstream system. Follow EXACTLY:

1. Use **plain Markdown only**. NO HTML tags. NO `<h1>`, `<p>`, `<style>`, no `<!DOCTYPE>`, no ```html fences. If you produce any HTML, the parser fails and the user sees raw tags.

2. Begin with an `## Executive Summary` section (3-4 sentences).

3. Follow with 3-5 titled sections using `## Section Title`. Use `##` (level 2) for ALL section headings — never `#`, never `###`.

4. Each section body is plain prose with optional bullet lists (`- item`). Cite sources inline as `[1]`, `[2]`, etc. matching the numbered sources list at the end.

5. **The LAST line of every section MUST be exactly:** `Confidence: NN%` (integer 0-100, no decimal, no extra punctuation, on its own line). This is mandatory — every section, no exceptions.

6. Add `## Flagged Claims` if there are any claims below 60% confidence — list them as bullets with reasons.

7. End with `## Sources` — a numbered list:
   ```
   ## Sources
   1. https://example.com/article-one
   2. https://example.com/article-two
   ```
   URLs only, one per line, with the number matching the inline `[N]` citations.

EXAMPLE of correct structure (do NOT copy the content, only the format):
```
## Executive Summary
Brief 3-4 sentence overview of findings.
Confidence: 85%

## Market Growth
The market grew 40% in 2025 [1] driven by enterprise adoption [2].
- Bullet point one
- Bullet point two
Confidence: 90%

## Sources
1. https://example.com/source-one
2. https://example.com/source-two
```

Do NOT wrap the output in code fences. Do NOT add a closing summary after Sources. Start your response with `## Executive Summary` on the very first line.""",
        expected_output="Strict markdown report: ## sections each ending with `Confidence: NN%`, final ## Sources list of URLs. No HTML, no code fences.",
        agent=writer,
        context=[fact_check_task],
    )

    return [research_task, analysis_task, fact_check_task, write_task]
