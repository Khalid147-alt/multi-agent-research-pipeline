import { motion } from "framer-motion"

const STATUS_STYLES = {
  idle: { dot: "bg-edge", ring: "border-edge", label: "Waiting" },
  active: { dot: "bg-accent", ring: "border-accent", label: "Working" },
  complete: { dot: "bg-ok", ring: "border-ok/40", label: "Complete" },
}

export default function AgentCard({ name, role, status, preview }) {
  const styles = STATUS_STYLES[status] || STATUS_STYLES.idle

  return (
    <motion.div
      layout
      className={`bg-panel border ${styles.ring} rounded-xl p-4 transition`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="relative">
          <div className={`w-2.5 h-2.5 rounded-full ${styles.dot}`} />
          {status === "active" && (
            <motion.div
              className={`absolute inset-0 rounded-full ${styles.dot}`}
              animate={{ scale: [1, 2.5], opacity: [0.6, 0] }}
              transition={{ duration: 1.4, repeat: Infinity }}
            />
          )}
        </div>
        <span className="text-xs text-muted uppercase tracking-wider">
          {styles.label}
        </span>
      </div>
      <div className="font-semibold">{name}</div>
      <div className="text-xs text-muted mt-1">{role}</div>
      {preview && (
        <div className="text-xs text-gray-400 mt-3 line-clamp-2 italic">
          {preview}
        </div>
      )}
    </motion.div>
  )
}
