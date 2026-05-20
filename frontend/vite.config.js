import { defineConfig, loadEnv } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const backend = env.VITE_BACKEND_URL || "http://localhost:8000"
  const wsBackend = env.VITE_BACKEND_WS_URL || "ws://localhost:8000"
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/research": backend,
        "/report": backend,
        "/history": backend,
        "/health": backend,
        "/ws": { target: wsBackend, ws: true },
      },
    },
  }
})
