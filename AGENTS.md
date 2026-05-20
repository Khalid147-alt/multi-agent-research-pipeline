# Research Pipeline — AGENTS.md

> **Read this first every session.** This is the source of truth for project state.
> Update the **Status** and **Session log** sections at the end of each work block.

## What this project is
Multi-agent research pipeline. Portfolio project #2 for Khalid (Upwork / job interviews).
User submits a topic → 4 CrewAI agents research, analyze, fact-check, write → live React
dashboard via WebSocket → cited report + confidence chart + PDF download.

Deployment targets:
- **Backend** → HuggingFace Spaces Docker, port 7860, `USE_SQLITE=true`
- **Frontend** → Vercel
- **Local dev** → Vite (`:5173`) + uvicorn (`:8000`) with SQLite or Postgres

## Status — current reality (updated 2026-05-14)

| Phase | What it is | Status |
|------:|------------|--------|
| 1 | Scaffold + DB layer (config, adapter, schemas) | ✅ verified |
| 2 | Tools (Tavily, Scraper, PDF) | ✅ Tavily & Scraper verified; PDF lazy-imports (Windows has no GTK, works on HF) |
| 3 | Agents + tasks + crew construction | ✅ verified on crewai 1.14 |
| 4 | WebSocket + callbacks + REST + main.py | ✅ verified (`/health`, `POST /research`, `/report/{id}/pdf`) |
| 5 | React dashboard | ✅ pre-existing implementation verified; `npm run dev` boots clean |
| 6 | Full E2E integration test | ✅ passed locally — 4 agents fired, report stored, complete event sent |
| 7 | HuggingFace deployment | ✅ live at `https://khalid147-research-pipeline-backend.hf.space` |
| 8 | Vercel frontend deployment | ✅ live at `https://research-pipeline-eta.vercel.app` |

**Production URLs**
- Frontend: https://research-pipeline-eta.vercel.app
- Backend:  https://khalid147-research-pipeline-backend.hf.space
- HF Space repo: https://huggingface.co/spaces/Khalid147/research-pipeline-backend
- Vercel project: research-pipeline (org khalid-hussains-projects-3458aa41)

**Deploy artifacts**
- HF staging dir: `D:\hf-space-research\` (Dockerfile, README.md with HF frontmatter, requirements.txt, plus full backend tree)
- HF secrets set via `HfApi.add_space_secret`: `GEMINI_API_KEY`, `TAVILY_API_KEY`
- HF variables: `USE_SQLITE=true`, `ENVIRONMENT=production`
- Vercel env (set at deploy time via `-e` and `--build-env`):
  `VITE_BACKEND_URL=https://khalid147-research-pipeline-backend.hf.space`,
  `VITE_BACKEND_WS_URL=wss://khalid147-research-pipeline-backend.hf.space`

## Stack (as actually installed — Python 3.13 venv at `.venv`)

- **Backend**: FastAPI 0.119, async Python 3.13
- **CrewAI**: 1.14.4 (the requirements floor was `>=`, PyPI no longer has 0.80 for Py 3.13)
- **LLMs**: `crewai.LLM` — all four agents on `gemini/gemini-2.5-flash` (see below for why)
- **Tools**: Tavily Python 0.7, BeautifulSoup4 4.12, WeasyPrint 68.1 (lazy-imported)
- **DB**: PostgreSQL/asyncpg 0.31 (local) or SQLite/aiosqlite 0.21 (HuggingFace)
- **Frontend**: React 18.3, Vite 5.4, TailwindCSS 3.4, Framer Motion 11, Recharts 2.13

### Why all-Gemini and not Groq

Original plan: Groq Llama for the Researcher. **It does not work in this environment.**
`crewai.LLM` natively supports openai / anthropic / google / gemini / bedrock / openrouter /
deepseek / ollama / cerebras / dashscope — **no native Groq**. Groq routing requires LiteLLM,
and LiteLLM's latest releases pin `openai==2.24.0` strictly, which conflicts with crewai's
`openai>=2.30,<3`. We tried, hit the hard pin, uninstalled litellm.

Current: all four agents use Gemini 2.5 Flash. Different temperatures (0.1 researcher,
0.3 others) provide the spread the original plan wanted. `GROQ_API_KEY` is no longer used.

If you want Groq back: use **Cerebras** (native crewai provider, free, serves Llama 3.3 70B)
or **OpenRouter** (native, proxies Groq). Don't reach for litellm again until they unpin openai.

## File layout

```
D:\multi-agents-system\
├── .env                            ← all 3 keys (GEMINI, GROQ, TAVILY)
├── .venv\                          ← active Python 3.13 venv
├── AGENTS.md                       ← this file
├── backend\
│   ├── .env                        ← copy of root .env (config.py loads from CWD)
│   ├── main.py                     ← FastAPI lifespan: init_schema + init_db_pool
│   ├── config.py                   ← pydantic-settings, lru_cache
│   ├── requirements.txt            ← local dev (has asyncpg)
│   ├── requirements.huggingface.txt← HF (no asyncpg, no redis)
│   ├── Dockerfile / Dockerfile.huggingface
│   ├── agents\
│   │   ├── llms.py                 ← get_gemini_llm(), get_researcher_llm() — both crewai.LLM
│   │   ├── researcher.py / analyst.py / fact_checker.py / writer.py
│   ├── crew\
│   │   ├── callbacks.py            ← ProgressListener(BaseEventListener) — see below
│   │   ├── tasks.py / research_crew.py
│   ├── tools\
│   │   ├── search_tool.py (TavilySearchTool)
│   │   ├── scraper_tool.py (ScraperTool, BeautifulSoup)
│   │   └── pdf_tool.py (PDFGeneratorTool, lazy WeasyPrint)
│   ├── api\
│   │   ├── research.py             ← POST /research, GET /report/{id}, /report/{id}/pdf, /history
│   │   ├── websocket.py            ← /ws/progress/{session_id}
│   │   └── health.py               ← /health (SQLite-aware)
│   ├── ws\manager.py               ← ConnectionManager + sessions dict (no Redis on HF)
│   └── db\
│       ├── adapter.py              ← dispatches asyncpg vs aiosqlite by USE_SQLITE env
│       ├── connection.py           ← asyncpg, with try/except ImportError at top
│       ├── sqlite_connection.py    ← aiosqlite with _SqlitePool shim (translates $1→?)
│       ├── schema.sql / sqlite_schema.sql
└── frontend\
    ├── package.json / vite.config.js / tailwind.config.js / vercel.json
    ├── index.html
    └── src\
        ├── App.jsx / main.jsx / index.css
        ├── hooks\useResearch.js    ← WebSocket state machine
        ├── lib\api.js              ← REST client; uses VITE_BACKEND_URL (empty in dev → Vite proxy)
        └── components\
            ├── TopicInput.jsx       ← animated example placeholders
            ├── AgentCard.jsx        ← idle/active/complete with pulse
            ├── ProgressBar.jsx      ← 0→100% with stage labels
            ├── AgentActivityFeed.jsx← AnimatePresence event stream
            ├── ConfidenceChart.jsx  ← Recharts horizontal bars
            ├── ReportViewer.jsx     ← parses markdown, extracts confidence per section
            ├── HistorySidebar.jsx   ← past sessions via GET /history
            └── PDFDownloadBtn.jsx
```

## Architecture conventions (load-bearing — break at your peril)

- **Never block the event loop**: `crew.kickoff()` always inside `asyncio.to_thread()`.
- **DB access**: import only from `db.adapter`, never from `db.connection` or
  `db.sqlite_connection` directly. The adapter picks the right pool based on `USE_SQLITE`.
- **asyncpg**: must be wrapped in `try/except ImportError` at every import site —
  it is NOT installed on HuggingFace.
- **WeasyPrint**: lazy-import only, inside the function that calls it. Module-level
  imports crash on Windows because GTK isn't installed.
- **Secrets**: only via `config.get_settings()` (pydantic-settings reads `.env`). Never hardcode.
- **No Redis on HF**: `ws/manager.py` keeps sessions in an in-memory `dict`.
- **CrewAI 1.14 LLMs**: pass `crewai.LLM(model="gemini/gemini-2.5-flash", api_key=...)`,
  never raw langchain objects (`ChatGoogleGenerativeAI`, `ChatGroq` etc. are rejected).
- **CrewAI 1.14 callbacks**: do NOT pass `callbacks=[...]` to `Agent(...)`. Use the global
  `crewai_event_bus` via a `BaseEventListener` subclass (see `crew/callbacks.py`).

## Progress event listener — how it works

`crew/callbacks.py::ProgressListener` is a `BaseEventListener` subclass. One instance is
constructed **per research session** in `research_crew.run_research()`. It:

1. Captures the FastAPI event loop at construction (`asyncio.get_running_loop()`).
2. Registers four handlers on `crewai_event_bus`:
   - `AgentExecutionStartedEvent` → emit `agent_start`
   - `ToolUsageStartedEvent` → emit `tool_use`
   - `ToolUsageFinishedEvent` → emit `tool_result`
   - `AgentExecutionCompletedEvent` → emit `agent_finish`
3. Bridges thread → loop via `asyncio.run_coroutine_threadsafe` (handlers run on the
   worker thread that crew.kickoff() executes on).
4. `cleanup()` (called in `finally`) removes handlers from the bus to prevent leaks
   across sessions.

CrewAI roles like `"Senior Research Analyst"` are mapped to short dashboard labels
(`"Researcher"`) via `_AGENT_PROGRESS` so the React side stays untouched.

## WebSocket wire format (frontend depends on this — don't change without updating React)

```
{"type":"agent_start",   "agent":"Researcher",   "task":"...",  "percent":0,   "timestamp":"..."}
{"type":"tool_use",      "agent":"Researcher",   "tool":"tavily_search", "preview":"...", "timestamp":"..."}
{"type":"tool_result",   "agent":"Researcher",   "tool":"tavily_search", "preview":"...", "timestamp":"..."}
{"type":"agent_finish",  "agent":"Researcher",   "preview":"...","percent":25, "timestamp":"..."}
{"type":"complete",      "report_id":"...",      "timestamp":"..."}
{"type":"error",         "message":"...",        "recoverable":false}
```

## Environment variables

| Var | Used for | Required where |
|-----|----------|----------------|
| `GEMINI_API_KEY` | all 4 agents (gemini-2.5-flash) | always |
| `TAVILY_API_KEY` | web search tool | always |
| `GROQ_API_KEY` | (currently unused — kept for future Cerebras/OpenRouter swap) | optional |
| `DATABASE_URL` | local Postgres only | local dev when `USE_SQLITE=false` |
| `USE_SQLITE` | toggles adapter to aiosqlite | `true` on HF; default `false` locally |
| `ENVIRONMENT` | logging hint | `production` on HF |
| `GEMINI_MODEL` | override (default `gemini-2.5-flash`) | optional |

## How to run locally

```powershell
# 1. activate venv (already exists)
.\.venv\Scripts\Activate.ps1

# 2. backend (terminal 1) — SQLite is simplest, no Docker needed
cd backend
$env:USE_SQLITE="true"
uvicorn main:app --port 8000
# verify:  curl http://localhost:8000/health  → {"status":"ok","db":"sqlite"}

# 3. frontend (terminal 2)
cd frontend
npm run dev
# open http://localhost:5173
```

Vite proxies `/research`, `/report`, `/history`, `/health`, `/ws` to `:8000`, so
`VITE_BACKEND_URL` and `VITE_BACKEND_WS_URL` can stay empty in dev.

## What's left

### Phase 6 — full E2E integration test
- Boot backend + frontend, submit a real topic, watch all 4 agents fire.
- Expected timing: 2–4 min, ~20 Gemini calls + ~5 Tavily searches.
- Free-tier Gemini limit is 15 req/min; should be fine since the crew runs sequentially.
- Check: dashboard updates live, report renders, confidence chart shows bars, PDF downloads
  (PDF will 503 on Windows local since no GTK — works on HF Docker).

### Phase 7 — HuggingFace Spaces deployment (`D:\hf-space-research\`)
- Copy `backend/*` → `D:\hf-space-research\`
- Use `Dockerfile.huggingface` (port 7860, `USE_SQLITE=true`, GTK system deps)
- Push to `https://huggingface.co/spaces/Khalid147/research-pipeline-backend`
- Add space secrets: `GEMINI_API_KEY`, `TAVILY_API_KEY`. Variables: `USE_SQLITE=true`, `ENVIRONMENT=production`
- Verify `https://khalid147-research-pipeline-backend.hf.space/health` returns sqlite OK
- **WebSocket on HF must be `wss://` not `ws://`** (HTTPS proxy)

### Phase 8 — Vercel frontend deployment
- `vercel --prod` from `frontend/`
- Env vars: `VITE_BACKEND_URL=https://khalid147-research-pipeline-backend.hf.space`,
  `VITE_BACKEND_WS_URL=wss://khalid147-research-pipeline-backend.hf.space`

### Known cleanups (defer until Phase 7)
- `requirements*.txt` still list `langchain-google-genai` and `langchain-groq` —
  unused since the crewai 1.14 migration. Strip before building the HF image to shrink layer size.
- `tasks.py` mentions Groq in the task descriptions; revisit for clarity.

## Session log (append a one-line entry per work block)

- **2026-05-20** — Production demo was broken. Real root cause was a missing
  pip package: CrewAI 1.14.4's native `gemini/` provider imports `google-genai`
  at runtime, but `requirements.huggingface.txt` only had the older
  `google-generativeai` (langchain bridge). Every research run died on the
  first `build_researcher()` call with `ImportError: Google Gen AI native
  provider not available`. Added `google-genai>=1.0.0` to both requirements
  files. Also fixed two latent bugs that made the failure look mysterious:
  (1) replaced `BackgroundTasks` with `asyncio.create_task` so the worker
  isn't tied to the request lifecycle on HF, and (2) added a `BaseException`
  safety-net wrapper around `run_research` plus a stuck-session reaper in
  `/history` that flips `running > 15 min` rows to `failed`. Frontend now
  logs `POST /research to:`, `POST /research response:`, `WS_BASE:`,
  `session_id:`, `Opening WebSocket:`, `WebSocket OPENED ✅`,
  `WebSocket CLOSED:`, `WebSocket ERROR ❌` to make prod debugging quick.
  E2E verified against the live stack: 4 agents finished in ~80s, real
  cited HTML report returned. Repo pushed to
  https://github.com/Khalid147-alt/multi-agent-research-pipeline (MIT,
  with LICENSE, issue/PR templates, CODEOWNERS).
- **2026-05-14** — Closed out Phases 6–8. Phase 6: E2E ran end-to-end against Gemini 2.5 Flash
  + Tavily, 4 agents finished and the report row landed in SQLite (PDF returns 503 locally as
  expected — no GTK on Windows). Fixed `main.py` to force UTF-8 stdout so CrewAI's emoji
  console boxes don't crash on Windows cp1252 (harmless on HF Linux). Stripped unused
  `langchain-*` / `groq` / `asyncpg` / `redis` from `requirements.huggingface.txt`. Phase 7:
  created HF Space `Khalid147/research-pipeline-backend`, uploaded backend + Dockerfile +
  README with HF frontmatter, set secrets/vars via `HfApi.add_space_secret/_variable`, Space
  is RUNNING and `/health` returns sqlite OK. First build failed because Dockerfile still
  COPYed `requirements.huggingface.txt` after I renamed it — fixed and re-uploaded. Phase 8:
  installed Vercel CLI, deployed `frontend/` with `VITE_BACKEND_URL` + `VITE_BACKEND_WS_URL`
  baked in at build time, prod alias is `research-pipeline-eta.vercel.app` (HTTP 200).
- **2026-05-12** — Verified Phases 1–5 on a fresh Python 3.13 install. Migrated to crewai 1.14
  (LLM = `crewai.LLM("gemini/...")`, callbacks = `BaseEventListener` on event bus). Switched
  researcher off Groq (LiteLLM/openai pin conflict) — all 4 agents now Gemini. Fixed
  `pdf_tool.py` to lazy-import WeasyPrint and use `tempfile.gettempdir()`. Replaced
  `/report/{id}/pdf` stub with on-demand WeasyPrint render with 503 fallback. Frontend
  pre-existed and was verified intact; `npm install` + `vite dev` clean.

## Do NOT (lessons from this session)

- Do not import `asyncpg` at module level — wrap in `try/except ImportError`.
- Do not import `weasyprint` at module level — lazy-import inside the function.
- Do not pass langchain LLM objects to `Agent(llm=...)` on crewai 1.14 — use `crewai.LLM` strings.
- Do not pass `callbacks=[...]` to `Agent(...)` on crewai 1.14 — subscribe via `crewai_event_bus`.
- Do not install `litellm` to add Groq — it pins `openai==2.24.0` and breaks crewai.
- Do not use synchronous `crew.kickoff()` in a FastAPI route.
- Do not hardcode API keys; do not use Redis on HF; do not use OpenAI.
- Do not edit `agents/*.py` to add a `callbacks` param back.
- Do not use `/tmp/` hardcoded — `tempfile.gettempdir()` is cross-platform.
