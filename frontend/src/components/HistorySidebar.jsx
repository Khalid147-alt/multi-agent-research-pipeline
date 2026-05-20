import { useEffect, useState } from "react"
import { getHistory } from "../lib/api"

export default function HistorySidebar({ onSelect, refreshKey }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    getHistory()
      .then((data) => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
  }, [refreshKey])

  return (
    <aside className="bg-panel border border-edge rounded-xl p-4 h-fit sticky top-4">
      <div className="text-xs uppercase tracking-wider text-muted mb-3">
        Recent research
      </div>
      {items.length === 0 ? (
        <div className="text-sm text-muted italic">No sessions yet.</div>
      ) : (
        <ul className="space-y-1">
          {items.slice(0, 10).map((s) => (
            <li key={s.id}>
              <button
                onClick={() => onSelect?.(s.id)}
                className="w-full text-left text-sm px-2 py-1.5 rounded hover:bg-edge truncate"
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
                </span>{" "}
                {s.topic}
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}
