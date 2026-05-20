import { AnimatePresence, motion } from "framer-motion"

const TYPE_LABEL = {
  agent_start: "▶ Agent started",
  tool_use: "⚙ Tool",
  tool_result: "← Result",
  agent_finish: "✓ Finished",
  complete: "★ Pipeline complete",
  error: "✗ Error",
}

const TYPE_COLOR = {
  agent_start: "text-accent",
  tool_use: "text-amber",
  tool_result: "text-gray-300",
  agent_finish: "text-ok",
  complete: "text-ok font-semibold",
  error: "text-red-400 font-semibold",
}

export default function AgentActivityFeed({ events }) {
  return (
    <div className="bg-panel border border-edge rounded-xl p-4 h-[320px] sm:h-[380px] lg:h-[420px] overflow-y-auto">
      <div className="text-xs uppercase tracking-wider text-muted mb-3">
        Live activity feed
      </div>
      {events.length === 0 ? (
        <div className="text-sm text-muted italic">
          Awaiting agent activity…
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence initial={false}>
            {events.map((e, i) => (
              <motion.div
                key={`${e.timestamp}-${i}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="text-sm border-l-2 border-edge pl-3 py-1"
              >
                <div className="flex items-baseline gap-2">
                  <span
                    className={`text-xs ${TYPE_COLOR[e.type] || "text-muted"}`}
                  >
                    {TYPE_LABEL[e.type] || e.type}
                  </span>
                  {e.agent && (
                    <span className="text-xs text-gray-400">{e.agent}</span>
                  )}
                </div>
                {(e.task || e.preview || e.tool || e.message) && (
                  <div className="text-xs text-gray-400 mt-0.5 font-mono break-words">
                    {e.tool && <span className="text-amber">{e.tool}: </span>}
                    {e.task || e.preview || e.message}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
