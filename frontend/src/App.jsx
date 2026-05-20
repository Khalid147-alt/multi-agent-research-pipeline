import { useMemo, useState } from "react"
import { Routes, Route, useNavigate } from "react-router-dom"
import { Helmet } from "react-helmet-async"
import { motion, AnimatePresence } from "framer-motion"
import TopicInput from "./components/TopicInput.jsx"
import AgentCard from "./components/AgentCard.jsx"
import ProgressBar from "./components/ProgressBar.jsx"
import AgentActivityFeed from "./components/AgentActivityFeed.jsx"
import ReportViewer from "./components/ReportViewer.jsx"
import HistorySidebar from "./components/HistorySidebar.jsx"
import ReportPage from "./pages/ReportPage.jsx"
import { useResearch } from "./hooks/useResearch.js"
import { metaFor } from "./lib/seo.js"

const AGENTS = [
  { key: "Researcher", role: "Searches the web, scrapes sources" },
  { key: "Analyst", role: "Cross-references, identifies conflicts" },
  { key: "Fact Checker", role: "Scores claims by confidence" },
  { key: "Writer", role: "Drafts the final cited report" },
]

function agentStatus(events, agentName, progress, state) {
  const lower = agentName.toLowerCase()
  const matching = events.filter((e) =>
    (e.agent || "").toLowerCase().includes(lower),
  )
  if (matching.some((e) => e.type === "agent_finish")) return "complete"
  if (matching.some((e) => e.type === "agent_start" || e.type === "tool_use"))
    return "active"
  if (state === "complete" && progress >= 100) return "complete"
  return "idle"
}

function agentPreview(events, agentName) {
  const lower = agentName.toLowerCase()
  const latest = events.find(
    (e) =>
      (e.agent || "").toLowerCase().includes(lower) &&
      (e.preview || e.task || e.tool),
  )
  if (!latest) return null
  return latest.preview || latest.task || latest.tool
}

function HomePage() {
  const navigate = useNavigate()
  const {
    state,
    events,
    report,
    progress,
    topic,
    sessionId,
    errorMsg,
    startResearch,
    reset,
  } = useResearch()

  const [drawerOpen, setDrawerOpen] = useState(false)
  const isRunning = state === "running"

  const cards = useMemo(
    () =>
      AGENTS.map((a) => ({
        ...a,
        status: agentStatus(events, a.key, progress, state),
        preview: agentPreview(events, a.key),
      })),
    [events, progress, state],
  )

  const meta = metaFor({})
  const onSelectHistory = (id) => {
    setDrawerOpen(false)
    navigate(`/report/${id}`)
  }

  return (
    <div className="min-h-screen px-4 sm:px-6 py-6 sm:py-8 max-w-7xl mx-auto">
      <Helmet>
        <title>{meta.title}</title>
        <meta name="description" content={meta.description} />
        <meta property="og:title" content={meta.og.title} />
        <meta property="og:description" content={meta.og.description} />
        <meta property="og:type" content={meta.og.type} />
        <meta property="og:site_name" content={meta.og.siteName} />
        <meta name="twitter:card" content={meta.twitter.card} />
      </Helmet>

      <header className="mb-6 sm:mb-8 flex items-center justify-between gap-3 flex-wrap">
        <div className="min-w-0 flex-1">
          <motion.h1
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl sm:text-3xl font-bold tracking-tight"
          >
            Research <span className="text-accent">Pipeline</span>
          </motion.h1>
          <p className="text-xs sm:text-sm text-muted mt-1">
            Four AI agents researching, analyzing, fact-checking & writing — live.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setDrawerOpen(true)}
            className="lg:hidden text-sm text-muted hover:text-white border border-edge px-3 py-2 rounded-lg min-h-[44px]"
            aria-label="Open history"
          >
            ☰ History
          </button>
          {state !== "idle" && (
            <button
              onClick={reset}
              className="text-sm text-muted hover:text-white border border-edge px-3 py-2 rounded-lg min-h-[44px]"
            >
              New research
            </button>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[260px,1fr] gap-6">
        <div className="hidden lg:block">
          <HistorySidebar
            refreshKey={state}
            onSelect={onSelectHistory}
          />
        </div>

        <AnimatePresence>
          {drawerOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setDrawerOpen(false)}
                className="lg:hidden fixed inset-0 bg-black/60 z-40"
              />
              <motion.aside
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "spring", stiffness: 240, damping: 28 }}
                className="lg:hidden fixed left-0 top-0 bottom-0 w-[85%] max-w-[320px] z-50 bg-bg border-r border-edge p-4 overflow-y-auto"
              >
                <div className="flex justify-between items-center mb-4">
                  <span className="text-sm font-semibold">History</span>
                  <button
                    onClick={() => setDrawerOpen(false)}
                    className="text-muted hover:text-white px-2 py-1 min-h-[44px] min-w-[44px]"
                    aria-label="Close history"
                  >
                    ✕
                  </button>
                </div>
                <HistorySidebar
                  refreshKey={state}
                  onSelect={onSelectHistory}
                  embedded
                />
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        <main className="space-y-6 min-w-0">
          <TopicInput onSubmit={startResearch} disabled={isRunning} />

          {state !== "idle" && (
            <>
              <div className="bg-panel border border-edge rounded-xl p-4">
                <div className="text-xs uppercase tracking-wider text-muted mb-1">
                  Researching
                </div>
                <div className="font-medium mb-3 break-words">{topic}</div>
                <ProgressBar percent={progress} />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {cards.map((a) => (
                  <AgentCard
                    key={a.key}
                    name={a.key}
                    role={a.role}
                    status={a.status}
                    preview={a.preview}
                  />
                ))}
              </div>

              <AgentActivityFeed events={events} />
            </>
          )}

          {state === "error" && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm break-words">
              {errorMsg || "Pipeline failed. See backend logs."}
            </div>
          )}

          {state === "complete" && report && (
            <ReportViewer report={report} sessionId={sessionId} />
          )}
        </main>
      </div>

      <footer className="text-xs text-muted mt-10 sm:mt-12 text-center px-2">
        Built with CrewAI · FastAPI · React. Portfolio project by Khalid Hussain.
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/report/:id" element={<ReportPage />} />
    </Routes>
  )
}
