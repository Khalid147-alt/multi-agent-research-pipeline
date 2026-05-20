import { useMemo, useState } from "react"
import { motion } from "framer-motion"
import ConfidenceChart from "./ConfidenceChart.jsx"
import PDFDownloadBtn from "./PDFDownloadBtn.jsx"

function parseSections(content) {
  if (!content) return []
  const lines = content.split("\n")
  const sections = []
  let current = null
  for (const line of lines) {
    const h = line.match(/^#{1,3}\s+(.+)/)
    if (h) {
      if (current) sections.push(current)
      current = { title: h[1].trim(), body: [], confidence: null }
      continue
    }
    if (current) {
      const conf = line.match(/Confidence:\s*(\d+)\s*%/i)
      if (conf) current.confidence = parseInt(conf[1], 10)
      current.body.push(line)
    }
  }
  if (current) sections.push(current)
  return sections
    .filter((s) => s.title.length > 0)
    .map((s) => ({ ...s, body: s.body.join("\n").trim() }))
}

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
      className={`text-xs px-2 py-0.5 rounded-md border ${color} font-mono`}
    >
      Confidence: {v}%
    </span>
  )
}

export default function ReportViewer({ report, sessionId }) {
  const [appendixOpen, setAppendixOpen] = useState(false)

  const sections = useMemo(
    () => parseSections(report?.content || ""),
    [report?.content],
  )
  const chartSections = sections.filter((s) => typeof s.confidence === "number")
  const flagged = sections.find((s) =>
    /flagged|appendix/i.test(s.title),
  )

  if (!report || !report.content) {
    return (
      <div className="bg-panel border border-edge rounded-xl p-8 text-center text-muted">
        Report will appear here once the pipeline completes.
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{report.topic}</h2>
        <PDFDownloadBtn sessionId={sessionId} />
      </div>

      {chartSections.length > 0 && <ConfidenceChart sections={chartSections} />}

      <div className="bg-panel border border-edge rounded-xl p-6 space-y-6">
        {sections.map((s, i) => (
          <section key={i}>
            <div className="flex items-baseline justify-between mb-2 gap-3">
              <h3 className="text-lg font-semibold">{s.title}</h3>
              {confidenceBadge(s.confidence)}
            </div>
            <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
              {s.body}
            </div>
          </section>
        ))}
      </div>

      {flagged && (
        <div className="bg-amber/5 border border-amber/30 rounded-xl p-4">
          <button
            onClick={() => setAppendixOpen((o) => !o)}
            className="w-full text-left flex justify-between items-center text-amber font-semibold"
          >
            <span>⚠ {flagged.title}</span>
            <span>{appendixOpen ? "▾" : "▸"}</span>
          </button>
          {appendixOpen && (
            <pre className="text-xs text-gray-300 mt-3 whitespace-pre-wrap font-mono">
              {flagged.body}
            </pre>
          )}
        </div>
      )}
    </motion.div>
  )
}
