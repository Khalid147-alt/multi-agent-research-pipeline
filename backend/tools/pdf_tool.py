import os
import tempfile

from crewai.tools import BaseTool


class PDFGeneratorTool(BaseTool):
    name: str = "generate_pdf"
    description: str = "Generate a PDF from HTML string. Returns file path."

    def _run(self, html_content: str) -> str:
        from weasyprint import HTML  # lazy import: WeasyPrint needs GTK on Windows
        out_dir = tempfile.gettempdir()
        path = os.path.join(out_dir, f"report_{os.urandom(4).hex()}.pdf")
        HTML(string=html_content).write_pdf(path)
        return path
