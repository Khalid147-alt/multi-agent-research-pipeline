import httpx
from bs4 import BeautifulSoup
from crewai.tools import BaseTool


class ScraperTool(BaseTool):
    name: str = "scrape_url"
    description: str = (
        "Scrape full text from a URL. Use after search for complete article content."
    )

    def _run(self, url: str) -> str:
        try:
            resp = httpx.get(
                url,
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)[:3000]
        except Exception as e:
            return f"Scrape failed: {str(e)}"
