// In dev, BASE is "" so requests go to the Vite proxy.
// In prod, prefer the build-time env; fall back to the known HF Space so
// requests never hit Vercel (which would 404) if the env var is missing.
const PROD_API_FALLBACK = "https://khalid147-research-pipeline-backend.hf.space"
const BASE =
  import.meta.env.VITE_BACKEND_URL ||
  (import.meta.env.PROD ? PROD_API_FALLBACK : "")

export async function startResearch(topic) {
  const res = await fetch(`${BASE}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
  })
  if (!res.ok) throw new Error(`startResearch failed: ${res.status}`)
  return res.json()
}

export async function getReport(sessionId) {
  const res = await fetch(`${BASE}/report/${sessionId}`)
  if (!res.ok) throw new Error(`getReport failed: ${res.status}`)
  return res.json()
}

export async function getHistory() {
  const res = await fetch(`${BASE}/history`)
  if (!res.ok) return []
  return res.json()
}

export async function downloadPdf(sessionId) {
  const res = await fetch(`${BASE}/report/${sessionId}/pdf`)
  if (!res.ok) throw new Error("PDF unavailable")
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `research-${sessionId}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
