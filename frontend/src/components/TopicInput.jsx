import { useEffect, useState } from "react"
import { motion } from "framer-motion"

const EXAMPLES = [
  "Impact of AI on software engineering jobs 2025",
  "Latest breakthroughs in fusion energy research",
  "Effectiveness of intermittent fasting for metabolic health",
  "How quantum computers will disrupt cryptography",
  "Economic effects of remote work post-2020",
]

export default function TopicInput({ onSubmit, disabled }) {
  const [value, setValue] = useState("")
  const [placeholderIdx, setPlaceholderIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => {
      setPlaceholderIdx((i) => (i + 1) % EXAMPLES.length)
    }, 3200)
    return () => clearInterval(t)
  }, [])

  const handle = (e) => {
    e.preventDefault()
    if (!value.trim() || disabled) return
    onSubmit(value.trim())
  }

  return (
    <form onSubmit={handle} className="w-full">
      {/* Stacked layout on mobile, overlay button on sm+ for that hero feel. */}
      <div className="flex flex-col sm:relative gap-2 sm:gap-0">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={`e.g. ${EXAMPLES[placeholderIdx]}`}
          disabled={disabled}
          maxLength={300}
          className="w-full bg-panel border border-edge rounded-xl px-4 sm:px-6 py-4 sm:py-5 text-base sm:text-lg
                     placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent
                     disabled:opacity-50 transition sm:pr-36"
        />
        <motion.button
          type="submit"
          disabled={disabled || !value.trim()}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="sm:absolute sm:right-2 sm:top-1/2 sm:-translate-y-1/2
                     bg-accent hover:bg-blue-500
                     disabled:bg-edge disabled:cursor-not-allowed
                     px-5 py-3 sm:py-2.5 rounded-lg font-medium transition min-h-[44px]"
        >
          Research →
        </motion.button>
      </div>
      <p className="text-xs text-muted mt-2 px-1">
        4 AI agents will search, analyze, fact-check, and write a cited report.
      </p>
    </form>
  )
}
