import { motion } from "framer-motion"

const STAGES = [
  { at: 0, label: "Searching" },
  { at: 25, label: "Analyzing" },
  { at: 50, label: "Fact-checking" },
  { at: 75, label: "Writing" },
  { at: 100, label: "Complete" },
]

export default function ProgressBar({ percent }) {
  const currentStage =
    STAGES.slice().reverse().find((s) => percent >= s.at)?.label || "Idle"

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-muted mb-2">
        <span>{currentStage}</span>
        <span>{Math.round(percent)}%</span>
      </div>
      <div className="h-2 bg-panel rounded-full overflow-hidden border border-edge">
        <motion.div
          className="h-full bg-gradient-to-r from-accent to-blue-400"
          animate={{ width: `${percent}%` }}
          transition={{ type: "spring", stiffness: 60, damping: 20 }}
        />
      </div>
    </div>
  )
}
