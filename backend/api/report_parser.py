"""
Parses the Writer agent's strict-markdown output into structured sections
and renders an inline SVG bar chart of per-section confidence for the PDF.

The Writer is instructed to emit:
  ## Section Title
  body paragraphs, [1] citations, optional bullets
  Confidence: NN%
  ...
  ## Sources
  1. https://...
  2. https://...

If the Writer drifts (older sessions, HTML, missing confidence), we degrade
gracefully so the UI still renders something readable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import List, Optional


_HEADING_RE = re.compile(r"^\s*##\s+(.+?)\s*$")
_CONF_RE = re.compile(r"^\s*Confidence:\s*(\d{1,3})\s*%\s*$", re.IGNORECASE)
_SOURCE_RE = re.compile(r"^\s*\d+\.\s*(https?://\S+)\s*$")
_INLINE_CITE_RE = re.compile(r"\[(\d+)\]")


@dataclass
class Section:
    title: str
    body: str
    confidence: Optional[int]

    def to_dict(self) -> dict:
        return {"title": self.title, "body": self.body, "confidence": self.confidence}


def _strip_html_fences(content: str) -> str:
    """Best-effort cleanup if the LLM ignored the no-HTML rule.
    Drops `<!DOCTYPE...>`, `<html>`, `<head>`, `<style>` blocks; flattens
    `<h1>X</h1>` into `## X` so legacy reports still parse.
    """
    if "<" not in content:
        return content
    # Drop full HTML wrappers
    content = re.sub(r"```html\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"```\s*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"<!DOCTYPE[^>]*>", "", content, flags=re.IGNORECASE)
    content = re.sub(
        r"<(html|head|body|style|script)[^>]*>", "", content, flags=re.IGNORECASE
    )
    content = re.sub(r"</(html|head|body|style|script)>", "", content, flags=re.IGNORECASE)
    # Convert h1/h2/h3 to markdown
    content = re.sub(r"<h1[^>]*>(.*?)</h1>", r"## \1", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1", content, flags=re.IGNORECASE | re.DOTALL)
    # Strip remaining tags
    content = re.sub(r"<[^>]+>", "", content)
    return content


def parse_sections(content: str) -> List[Section]:
    if not content:
        return []
    cleaned = _strip_html_fences(content)
    sections: List[Section] = []
    current_title: Optional[str] = None
    current_lines: list[str] = []
    current_conf: Optional[int] = None

    def flush():
        nonlocal current_title, current_lines, current_conf
        if current_title is None:
            return
        body = "\n".join(current_lines).strip()
        sections.append(Section(title=current_title, body=body, confidence=current_conf))
        current_title = None
        current_lines = []
        current_conf = None

    for raw_line in cleaned.split("\n"):
        line = raw_line.rstrip()
        h = _HEADING_RE.match(line)
        if h:
            flush()
            current_title = h.group(1).strip()
            continue
        if current_title is None:
            continue  # discard preamble before first heading
        c = _CONF_RE.match(line)
        if c:
            try:
                current_conf = max(0, min(100, int(c.group(1))))
            except ValueError:
                pass
            continue  # don't include the confidence line in body
        current_lines.append(raw_line)
    flush()
    return sections


def extract_sources(content: str) -> List[str]:
    """Pull URLs from the trailing ## Sources section."""
    if not content:
        return []
    cleaned = _strip_html_fences(content)
    in_sources = False
    urls: list[str] = []
    for raw_line in cleaned.split("\n"):
        line = raw_line.strip()
        if _HEADING_RE.match(line):
            in_sources = line.lower().endswith("sources")
            continue
        if not in_sources:
            continue
        m = _SOURCE_RE.match(line)
        if m:
            urls.append(m.group(1))
    return urls


def chart_data(sections: List[Section]) -> List[dict]:
    """Per-section confidence in the shape the frontend expects."""
    out = []
    for s in sections:
        if s.confidence is None:
            continue
        # Skip non-content sections
        low = s.title.strip().lower()
        if low in {"sources", "flagged claims"}:
            continue
        out.append({"name": s.title, "confidence": s.confidence})
    return out


# ----- PDF rendering --------------------------------------------------------

_PDF_CSS = """
@page { size: A4; margin: 22mm 18mm; }
* { box-sizing: border-box; }
body { font-family: 'Helvetica', 'Arial', sans-serif; color: #111; line-height: 1.55; font-size: 11pt; }
h1 { font-size: 22pt; margin: 0 0 4pt; color: #0f172a; }
h2 { font-size: 14pt; margin: 18pt 0 6pt; color: #1f3a8a; border-bottom: 1px solid #e5e7eb; padding-bottom: 3pt; }
h3 { font-size: 12pt; margin: 12pt 0 4pt; color: #334155; }
p  { margin: 4pt 0; }
ul, ol { margin: 4pt 0 4pt 18pt; padding: 0; }
li { margin: 2pt 0; }
a { color: #1d4ed8; text-decoration: none; }
.meta { color: #64748b; font-size: 9pt; margin-bottom: 14pt; }
.chart-wrap { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6pt; padding: 10pt; margin: 12pt 0; }
.chart-title { font-size: 10pt; color: #334155; font-weight: 600; margin-bottom: 6pt; text-transform: uppercase; letter-spacing: 0.5pt; }
.confidence-badge { display: inline-block; font-size: 9pt; padding: 1pt 6pt; border-radius: 8pt; background: #eef2ff; color: #3730a3; margin-left: 6pt; }
.confidence-high { background: #d1fae5; color: #065f46; }
.confidence-mid  { background: #dbeafe; color: #1e3a8a; }
.confidence-low  { background: #fef3c7; color: #92400e; }
.section { page-break-inside: avoid; }
.footer { color: #94a3b8; font-size: 8pt; margin-top: 22pt; border-top: 1px solid #e5e7eb; padding-top: 6pt; text-align: center; }
"""


def _bar_color(v: int) -> str:
    if v >= 80:
        return "#10b981"
    if v >= 60:
        return "#3b82f6"
    return "#f59e0b"


def _badge_class(v: Optional[int]) -> str:
    if v is None:
        return ""
    if v >= 80:
        return "confidence-high"
    if v >= 60:
        return "confidence-mid"
    return "confidence-low"


def render_confidence_svg(data: List[dict], width: int = 520, row_h: int = 28) -> str:
    """Inline SVG horizontal bar chart. Renders inside WeasyPrint without
    any external image generation. Each entry is {name, confidence}.
    """
    if not data:
        return ""
    pad_left = 160
    pad_right = 50
    pad_top = 10
    pad_bot = 10
    height = pad_top + pad_bot + row_h * len(data)
    bar_max = width - pad_left - pad_right

    rows_svg = []
    for i, row in enumerate(data):
        y = pad_top + i * row_h
        v = max(0, min(100, int(row["confidence"])))
        bar_w = int(bar_max * v / 100)
        label = escape(str(row["name"])[:32])
        rows_svg.append(
            f'<text x="{pad_left - 8}" y="{y + row_h/2 + 4}" '
            f'text-anchor="end" font-size="10" fill="#334155">{label}</text>'
            f'<rect x="{pad_left}" y="{y + 6}" width="{bar_max}" height="{row_h - 12}" '
            f'fill="#f1f5f9" rx="3" />'
            f'<rect x="{pad_left}" y="{y + 6}" width="{bar_w}" height="{row_h - 12}" '
            f'fill="{_bar_color(v)}" rx="3" />'
            f'<text x="{pad_left + bar_w + 6}" y="{y + row_h/2 + 4}" '
            f'font-size="10" fill="#0f172a" font-weight="600">{v}%</text>'
        )
    return (
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        + "".join(rows_svg)
        + "</svg>"
    )


def render_pdf_html(topic: str, content: str) -> str:
    """Convert the Writer's strict markdown into a styled PDF-ready HTML.

    Pipeline:
      1. Strip any HTML the LLM drifted into.
      2. Parse sections + sources.
      3. Render a server-side SVG confidence chart.
      4. Use markdown-it-py to convert per-section body markdown to HTML.
      5. Wrap in styled <html> with print-friendly CSS.
    """
    sections = parse_sections(content)
    sources = extract_sources(content)
    chart = chart_data(sections)

    # markdown-it-py is in requirements; if it's missing we degrade to pre.
    try:
        from markdown_it import MarkdownIt

        md = MarkdownIt("commonmark", {"breaks": True, "linkify": True}).enable(
            ["table", "strikethrough"]
        )
        render_md = md.render
    except Exception:  # pragma: no cover
        def render_md(text: str) -> str:
            return f"<pre>{escape(text)}</pre>"

    section_html: list[str] = []
    for s in sections:
        if s.title.strip().lower() == "sources":
            continue  # render sources separately
        badge = ""
        if s.confidence is not None:
            badge = (
                f'<span class="confidence-badge {_badge_class(s.confidence)}">'
                f"Confidence: {s.confidence}%</span>"
            )
        body_html = render_md(s.body or "")
        section_html.append(
            f'<div class="section"><h2>{escape(s.title)}{badge}</h2>{body_html}</div>'
        )

    sources_html = ""
    if sources:
        items = "".join(
            f'<li><a href="{escape(u)}">{escape(u)}</a></li>' for u in sources
        )
        sources_html = f'<div class="section"><h2>Sources</h2><ol>{items}</ol></div>'

    chart_html = ""
    if chart:
        chart_html = (
            '<div class="chart-wrap">'
            '<div class="chart-title">Confidence per section</div>'
            + render_confidence_svg(chart)
            + "</div>"
        )

    safe_topic = escape(topic or "Research Report")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>{_PDF_CSS}</style></head>
<body>
<h1>{safe_topic}</h1>
<div class="meta">Generated by Multi-Agent Research Pipeline</div>
{chart_html}
{''.join(section_html)}
{sources_html}
<div class="footer">Research Pipeline · 4 AI agents · Researcher, Analyst, Fact-Checker, Writer</div>
</body></html>"""
