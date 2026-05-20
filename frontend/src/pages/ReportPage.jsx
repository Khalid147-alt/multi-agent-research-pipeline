import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Helmet } from "react-helmet-async"
import { motion } from "framer-motion"
import ReportViewer from "../components/ReportViewer.jsx"
import { getReportById } from "../lib/api.js"
import { metaFor } from "../lib/seo.js"

export default function ReportPage() {
  const { id } = useParams()
  const [report, setReport] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErr(null)
    getReportById(id)
      .then((data) => {
        if (!cancelled) setReport(data)
      })
      .catch((e) => {
        if (!cancelled) setErr(String(e.message || e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  const meta = metaFor({
    title: report?.topic || "Research report",
    description: report?.topic
      ? `AI-generated research report on "${report.topic}" — cited, fact-checked, with confidence scores.`
      : undefined,
    type: "article",
  })

  return (
    <div className="min-h-screen px-4 sm:px-6 py-6 sm:py-8 max-w-5xl mx-auto">
      <Helmet>
        <title>{meta.title}</title>
        <meta name="description" content={meta.description} />
        <meta property="og:title" content={meta.og.title} />
        <meta property="og:description" content={meta.og.description} />
        <meta property="og:type" content={meta.og.type} />
        <meta property="og:url" content={meta.og.url} />
        <meta property="og:site_name" content={meta.og.siteName} />
        <meta name="twitter:card" content={meta.twitter.card} />
        <meta name="twitter:title" content={meta.twitter.title} />
        <meta name="twitter:description" content={meta.twitter.description} />
      </Helmet>

      <header className="mb-6 flex items-center justify-between gap-3">
        <Link
          to="/"
          className="text-sm text-muted hover:text-white border border-edge px-3 py-2 rounded-lg min-h-[44px] inline-flex items-center"
        >
          ← New research
        </Link>
        <span className="text-xs text-muted font-mono break-all">
          /report/{id}
        </span>
      </header>

      {loading && (
        <div className="bg-panel border border-edge rounded-xl p-8 text-center text-muted">
          Loading report…
        </div>
      )}
      {err && !loading && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm">
          Couldn't load report: {err}
        </div>
      )}
      {!loading && !err && report && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <ReportViewer report={report} sessionId={id} />
        </motion.div>
      )}
    </div>
  )
}
