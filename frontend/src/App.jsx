import { useMemo } from "react"
import { motion } from "framer-motion"
import TopicInput from "./components/TopicInput.jsx"
import AgentCard from "./components/AgentCard.jsx"
import ProgressBar from "./components/ProgressBar.jsx"
import AgentActivityFeed from "./components/AgentActivityFeed.jsx"
import ReportViewer from "./components/ReportViewer.jsx"
import HistorySidebar from "./components/HistorySidebar.jsx"
import { useResearch } from "./hooks/useResearch.js"

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

export default function App() {
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

  return (
    <div className="min-h-screen px-6 py-8 max-w-7xl mx-auto">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold tracking-tight"
          >
            Research <span className="text-accent">Pipeline</span>
          </motion.h1>
          <p className="text-sm text-muted mt-1">
            Four AI agents researching, analyzing, fact-checking & writing — live.
          </p>
        </div>
        {state !== "idle" && (
          <button
            onClick={reset}
            className="text-sm text-muted hover:text-white border border-edge px-3 py-1.5 rounded-lg"
          >
            New research
          </button>
        )}
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[260px,1fr] gap-6">
        <HistorySidebar refreshKey={state} />

        <main className="space-y-6">
          <TopicInput onSubmit={startResearch} disabled={isRunning} />

          {state !== "idle" && (
            <>
              <div className="bg-panel border border-edge rounded-xl p-4">
                <div className="text-xs uppercase tracking-wider text-muted mb-1">
                  Researching
                </div>
                <div className="font-medium mb-3">{topic}</div>
                <ProgressBar percent={progress} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
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
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm">
              {errorMsg || "Pipeline failed. See backend logs."}
            </div>
          )}

          {state === "complete" && report && (
            <ReportViewer report={report} sessionId={sessionId} />
          )}
        </main>
      </div>

      <footer className="text-xs text-muted mt-12 text-center">
        Built with CrewAI · FastAPI · React. Portfolio project by Khalid.
      </footer>
    </div>
  )
}
