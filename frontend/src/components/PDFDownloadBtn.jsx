import { useState } from "react"
import { downloadPdf } from "../lib/api"

export default function PDFDownloadBtn({ sessionId }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const handle = async () => {
    if (!sessionId) return
    setBusy(true)
    setErr(null)
    try {
      await downloadPdf(sessionId)
    } catch (e) {
      setErr(String(e.message || e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      {err && <span className="text-xs text-red-400">{err}</span>}
      <button
        onClick={handle}
        disabled={!sessionId || busy}
        className="text-sm bg-edge hover:bg-edge/70 border border-edge
                   px-3 py-1.5 rounded-lg disabled:opacity-50"
      >
        {busy ? "Generating…" : "↓ PDF"}
      </button>
    </div>
  )
}
