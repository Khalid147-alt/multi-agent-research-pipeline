import { useMemo, useState } from "react"
import { motion } from "framer-motion"
import ConfidenceChart from "./ConfidenceChart.jsx"
import PDFDownloadBtn from "./PDFDownloadBtn.jsx"
import ShareBar from "./ShareBar.jsx"

function confidenceBadge(v) {
  if (v == null) return null
  const color =
    v >= 80
      ? "bg-ok/15 text-ok border-ok/30"
      : v >= 60
      ? "bg-accent/15 text-accent border-accent/30"
      : "bg-amber/15 text-amber border-amber/30"
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-md border ${color} font-mono whitespace-nowrap`}
    >
      Confidence: {v}%
    </span>
  )
}

// Render lightweight inline markdown for section bodies: paragraphs, bullet
// lists, and inline `[N]` citations. We avoid pulling a full markdown lib on
// the frontend — server-side parsing already chunked content into sections.
function renderBody(body) {
  if (!body) return null
  const lines = body.split("\n")
  const blocks = []
  let bullets = []
  let para = []

  const flushPara = () => {
    if (para.length === 0) return
    blocks.push({ kind: "p", text: para.join(" ") })
    para = []
  }
  const flushBullets = () => {
    if (bullets.length === 0) return
    blocks.push({ kind: "ul", items: bullets })
    bullets = []
  }

  for (const raw of lines) {
    const line = raw.trim()
    if (!line) {
      flushPara()
      flushBullets()
      continue
    }
    if (/^[-*]\s+/.test(line)) {
      flushPara()
      bullets.push(line.replace(/^[-*]\s+/, ""))
      continue
    }
    flushBullets()
    para.push(line)
  }
  flushPara()
  flushBullets()

  const linkify = (text) =>
    text.split(/(\[\d+\])/g).map((chunk, i) =>
      /\[\d+\]/.test(chunk) ? (
        <sup key={i} className="text-accent ml-0.5">
          {chunk}
        </sup>
      ) : (
        <span key={i}>{chunk}</span>
      ),
    )

  return (
    <div className="space-y-3 text-sm sm:text-[15px] text-gray-300 leading-relaxed">
      {blocks.map((b, i) =>
        b.kind === "p" ? (
          <p key={i}>{linkify(b.text)}</p>
        ) : (
          <ul key={i} className="list-disc list-outside pl-5 space-y-1">
            {b.items.map((it, j) => (
              <li key={j}>{linkify(it)}</li>
            ))}
          </ul>
        ),
      )}
    </div>
  )
}

export default function ReportViewer({ report, sessionId }) {
  const [appendixOpen, setAppendixOpen] = useState(false)

  const sections = report?.parsed_sections || []
  const chart = report?.chart_data || []
  const sources = report?.sources || []
  const flagged = useMemo(
    () => sections.find((s) => /flagged/i.test(s.title)),
    [sections],
  )

  if (!report || !report.content) {
    return (
      <div className="bg-panel border border-edge rounded-xl p-8 text-center text-muted">
        Report will appear here once the pipeline completes.
      </div>
    )
  }

  // Sections to render in the body — exclude Sources (rendered as a list) and
  // Flagged (rendered as collapsible appendix below).
  const bodySections = sections.filter(
    (s) =>
      !/^sources$/i.test(s.title.trim()) &&
      !/flagged/i.test(s.title.trim()),
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h2 className="text-xl sm:text-2xl font-bold break-words">{report.topic}</h2>
        <div className="flex items-center gap-2 shrink-0">
          <PDFDownloadBtn sessionId={sessionId} />
        </div>
      </div>

      {chart.length > 0 && (
        <ConfidenceChart
          sections={chart.map((c) => ({ title: c.name, confidence: c.confidence }))}
        />
      )}

      <div className="bg-panel border border-edge rounded-xl p-4 sm:p-6 space-y-6">
        {bodySections.map((s, i) => (
          <section key={i}>
            <div className="flex flex-wrap items-baseline justify-between mb-2 gap-2">
              <h3 className="text-base sm:text-lg font-semibold">{s.title}</h3>
              {confidenceBadge(s.confidence)}
            </div>
            {renderBody(s.body)}
          </section>
        ))}
      </div>

      {flagged && (
        <div className="bg-amber/5 border border-amber/30 rounded-xl p-4">
          <button
            onClick={() => setAppendixOpen((o) => !o)}
            className="w-full text-left flex justify-between items-center text-amber font-semibold min-h-[44px]"
          >
            <span>⚠ {flagged.title}</span>
            <span>{appendixOpen ? "▾" : "▸"}</span>
          </button>
          {appendixOpen && (
            <div className="mt-3 text-sm text-gray-300">
              {renderBody(flagged.body)}
            </div>
          )}
        </div>
      )}

      {sources.length > 0 && (
        <div className="bg-panel border border-edge rounded-xl p-4 sm:p-6">
          <h3 className="text-sm uppercase tracking-wider text-muted mb-3">
            Sources
          </h3>
          <ol className="space-y-1.5 text-sm">
            {sources.map((u, i) => (
              <li key={i} className="break-all">
                <span className="text-muted mr-2">[{i + 1}]</span>
                <a
                  href={u}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent hover:underline"
                >
                  {u}
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}

      <ShareBar topic={report.topic} sessionId={sessionId} />
    </motion.div>
  )
}
