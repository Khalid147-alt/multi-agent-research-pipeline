---
title: Research Pipeline Backend
emoji: 🔬
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Research Pipeline Backend

Multi-agent CrewAI research API.

- `POST /research` — kick off a research session
- `GET /report/{id}` — fetch finished report
- `GET /report/{id}/pdf` — download PDF
- `GET /history` — past sessions
- `WS /ws/progress/{session_id}` — live progress events
- `GET /health` — liveness

Secrets required (set in Space settings): `GEMINI_API_KEY`, `TAVILY_API_KEY`.
Variables: `USE_SQLITE=true`, `ENVIRONMENT=production`.
