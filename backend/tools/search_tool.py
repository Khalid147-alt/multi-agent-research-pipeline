from crewai.tools import BaseTool
from tavily import TavilyClient

from config import get_settings


class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = (
        "Search the web for current information. Returns URLs, titles, content."
    )

    def _run(self, query: str) -> str:
        settings = get_settings()
        client = TavilyClient(api_key=settings.tavily_api_key)
        results = client.search(
            query=query,
            max_results=settings.max_search_results,
            include_raw_content=True,
        )
        output = []
        for r in results.get("results", []):
            output.append(
                f"SOURCE: {r['url']}\nTITLE: {r['title']}\n"
                f"CONTENT: {r.get('content', '')[:800]}\n"
            )
        return "\n---\n".join(output)
