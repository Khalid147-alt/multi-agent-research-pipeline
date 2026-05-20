# Multi-Agent Research Pipeline

A production-grade multi-agent research system. Submit a topic, and four CrewAI agents — **Researcher**, **Analyst**, **Fact-Checker**, and **Writer** — collaborate to produce a cited report with per-section confidence scores, streamed live to a React dashboard over WebSocket and downloadable as a PDF.

**Live demo**
- Frontend: https://research-pipeline-eta.vercel.app
- Backend:  https://khalid147-research-pipeline-backend.hf.space

---

## What it does

1. User submits a research topic from the dashboard.
2. The backend spins up a CrewAI crew of four sequential agents:
   - **Researcher** — searches the web via Tavily, scrapes promising sources.
   - **Analyst** — extracts key claims, themes, and quantitative findings.
   - **Fact-Checker** — independently verifies claims and assigns per-section confidence.
   - **Writer** — synthesizes the verified material into a cited markdown report.
3. Each agent step (`agent_start`, `tool_use`, `tool_result`, `agent_finish`) is pushed over a WebSocket so the dashboard renders progress live.
4. The finished report is persisted, viewable in-app with a confidence chart, and exportable as a PDF.
5. Past sessions are listed in the history sidebar and can be reopened.

---

## Architecture

```
React + Vite (Vercel)
        │  WebSocket  +  REST
        ▼
FastAPI (HuggingFace Spaces, Docker)
        │
        ├── CrewAI 1.14 sequential crew (4 agents)
        │     ├── Tavily search tool
        │     ├── BeautifulSoup scraper tool
        │     └── WeasyPrint PDF tool (lazy-loaded)
        │
        ├── WebSocket manager (per-session in-memory)
        │     └── ProgressListener bridges crewai_event_bus → asyncio loop
        │
        └── DB adapter
              ├── PostgreSQL / asyncpg   (local dev)
              └── SQLite  / aiosqlite    (HuggingFace, USE_SQLITE=true)
```

### Stack

| Layer    | Tech |
|----------|------|
| Backend  | FastAPI 0.119, Python 3.13, async throughout |
| Agents   | CrewAI 1.14, Gemini 2.5 Flash (all four agents, different temperatures) |
| Tools    | Tavily, BeautifulSoup4, WeasyPrint |
| DB       | asyncpg (Postgres) or aiosqlite (SQLite) — chosen at runtime via `USE_SQLITE` |
| Frontend | React 18, Vite 5, Tailwind 3, Framer Motion, Recharts |
| Deploy   | HuggingFace Spaces (Docker, port 7860) + Vercel |

---

## Running locally

Requires Python 3.13 and Node 18+.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# create .env from the example and fill in your keys
copy ..\.env.example .env
# edit .env — set GEMINI_API_KEY, TAVILY_API_KEY at minimum

# SQLite mode is the simplest path (no Docker / no Postgres needed)
$env:USE_SQLITE="true"
uvicorn main:app --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok","db":"sqlite"}`.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

Vite proxies `/research`, `/report`, `/history`, `/health`, and `/ws` to `:8000`, so the frontend `VITE_BACKEND_URL` / `VITE_BACKEND_WS_URL` can stay empty in local dev.

---

## Required API keys

| Variable | Where to get it | Required |
|----------|-----------------|----------|
| `GEMINI_API_KEY` | https://aistudio.google.com/ | ✅ |
| `TAVILY_API_KEY` | https://app.tavily.com/ | ✅ |
| `GROQ_API_KEY` | https://console.groq.com/ | optional (unused since CrewAI 1.14 migration) |

Free tiers are sufficient for normal use.

---

## Deployment

### HuggingFace Spaces (backend)

- Dockerfile: `backend/Dockerfile.huggingface`
- Port: `7860`
- Variables: `USE_SQLITE=true`, `ENVIRONMENT=production`
- Secrets: `GEMINI_API_KEY`, `TAVILY_API_KEY`
- WebSocket URL must use `wss://` (HF proxies HTTPS).

### Vercel (frontend)

```powershell
cd frontend
vercel --prod \
  -e VITE_BACKEND_URL=https://your-space.hf.space \
  -e VITE_BACKEND_WS_URL=wss://your-space.hf.space
```

---

## Project layout

```
multi-agents-system/
├── backend/
│   ├── main.py                  FastAPI app + lifespan (DB init)
│   ├── config.py                pydantic-settings
│   ├── agents/                  researcher / analyst / fact_checker / writer
│   ├── crew/                    tasks, crew construction, ProgressListener
│   ├── tools/                   Tavily, scraper, PDF (lazy WeasyPrint)
│   ├── api/                     /research, /report, /history, /health, /ws
│   ├── ws/manager.py            in-memory connection manager
│   ├── db/                      adapter, asyncpg + aiosqlite backends
│   ├── requirements.txt         local dev
│   ├── requirements.huggingface.txt
│   └── Dockerfile.huggingface
└── frontend/
    └── src/
        ├── App.jsx
        ├── hooks/useResearch.js   WebSocket state machine
        ├── lib/api.js
        └── components/            TopicInput, AgentCard, ProgressBar,
                                   AgentActivityFeed, ConfidenceChart,
                                   ReportViewer, HistorySidebar, PDFDownloadBtn
```

See [`AGENTS.md`](AGENTS.md) for full architecture notes, conventions, and the project's session log.

---

## License

MIT
