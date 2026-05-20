import { useEffect, useState } from "react"
import { getHistory } from "../lib/api"

export default function HistorySidebar({ onSelect, refreshKey, embedded = false }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    getHistory()
      .then((data) => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
  }, [refreshKey])

  const wrapperClass = embedded
    ? ""
    : "bg-panel border border-edge rounded-xl p-4 h-fit sticky top-4"

  return (
    <aside className={wrapperClass}>
      {!embedded && (
        <div className="text-xs uppercase tracking-wider text-muted mb-3">
          Recent research
        </div>
      )}
      {items.length === 0 ? (
        <div className="text-sm text-muted italic">No sessions yet.</div>
      ) : (
        <ul className="space-y-1">
          {items.slice(0, 20).map((s) => (
            <li key={s.id}>
              <button
                onClick={() => onSelect?.(s.id)}
                className="w-full text-left text-sm px-2 py-2 rounded hover:bg-edge truncate min-h-[44px] flex items-center gap-2"
                title={s.topic}
              >
                <span
                  className={
                    s.status === "complete"
                      ? "text-ok"
                      : s.status === "failed"
                      ? "text-red-400"
                      : "text-amber"
                  }
                >
                  ●
                </span>
                <span className="truncate">{s.topic}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}
