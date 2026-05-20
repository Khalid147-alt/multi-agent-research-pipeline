import { useState, useRef, useCallback } from "react"
import * as api from "../lib/api"

// Resolve the WebSocket base URL.
//   1. VITE_BACKEND_WS_URL baked at build time (Vercel/Vite) — preferred.
//   2. In production, fall back to the known HuggingFace Space so the app
//      never silently tries to open `wss://<vercel-host>/ws/...`, which 404s.
//   3. In dev (Vite proxy), fall back to the current host with the right scheme.
const PROD_WS_FALLBACK = "wss://khalid147-research-pipeline-backend.hf.space"
const WS_BASE =
  import.meta.env.VITE_BACKEND_WS_URL ||
  (import.meta.env.PROD
    ? PROD_WS_FALLBACK
    : typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`
    : "")

export function useResearch() {
  const [state, setState] = useState("idle") // idle | running | complete | error
  const [events, setEvents] = useState([])
  const [report, setReport] = useState(null)
  const [progress, setProgress] = useState(0)
  const [topic, setTopic] = useState("")
  const [sessionId, setSessionId] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const wsRef = useRef(null)

  const startResearch = useCallback(async (newTopic) => {
    console.log("[research] start", { topic: newTopic })
    console.log("[research] env", {
      VITE_BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
      VITE_BACKEND_WS_URL: import.meta.env.VITE_BACKEND_WS_URL,
      WS_BASE,
      PROD: import.meta.env.PROD,
    })
    setState("running")
    setEvents([])
    setReport(null)
    setProgress(0)
    setErrorMsg(null)
    setTopic(newTopic)

    let session
    try {
      session = await api.startResearch(newTopic)
      console.log("[research] POST /research response:", session)
    } catch (e) {
      console.error("[research] POST /research failed:", e)
      setState("error")
      setErrorMsg(String(e.message || e))
      return
    }
    if (!session?.session_id) {
      console.error("[research] no session_id in response, aborting WS open")
      setState("error")
      setErrorMsg("Backend did not return a session_id")
      return
    }
    setSessionId(session.session_id)

    const wsUrl = `${WS_BASE}/ws/progress/${session.session_id}`
    console.log("[research] opening WebSocket:", wsUrl)
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    console.log("[research] WebSocket constructed, readyState:", ws.readyState)

    ws.onopen = () => console.log("[research] WS open ✅", wsUrl)
    ws.onclose = (e) =>
      console.log("[research] WS close", { code: e.code, reason: e.reason, wasClean: e.wasClean })

    ws.onmessage = async (e) => {
      let event
      try {
        event = JSON.parse(e.data)
      } catch {
        return
      }
      setEvents((prev) => [event, ...prev].slice(0, 200))
      if (typeof event.percent === "number") setProgress(event.percent)

      if (event.type === "complete") {
        setState("complete")
        setProgress(100)
        ws.close()
        try {
          const data = await api.getReport(event.report_id)
          setReport(data)
        } catch (err) {
          setErrorMsg(String(err.message || err))
        }
      }
      if (event.type === "error") {
        setState("error")
        setErrorMsg(event.message || "Unknown error")
        ws.close()
      }
    }

    ws.onerror = (e) => {
      console.error("[research] WS error ❌", e, "url:", wsUrl)
      setState("error")
      setErrorMsg("WebSocket connection failed")
    }
  }, [])

  const cancel = useCallback(() => {
    wsRef.current?.close()
    setState("idle")
  }, [])

  const reset = useCallback(() => {
    wsRef.current?.close()
    setState("idle")
    setEvents([])
    setReport(null)
    setProgress(0)
    setTopic("")
    setSessionId(null)
    setErrorMsg(null)
  }, [])

  return {
    state,
    events,
    report,
    progress,
    topic,
    sessionId,
    errorMsg,
    startResearch,
    cancel,
    reset,
  }
}
