# Security policy

This is a public portfolio project. It runs untrusted input (user-supplied
research topics) through an LLM and renders the output back to a browser.
The following hardenings are in place and the following gaps are
documented.

## Reporting a vulnerability

If you find a vulnerability, please email **sindhikhalid126@gmail.com** with:

- A description of the issue
- Steps to reproduce
- The impact you believe it has

Please do **not** open a public GitHub issue for security problems. I'll
respond within a few days and credit you in the fix unless you'd rather
stay anonymous.

## What is mitigated

| Class | Mitigation |
|---|---|
| **Injection (OWASP A03)** | Topic input is Pydantic-validated: 5–300 chars, ASCII control chars stripped, HTML brackets rejected. SQLite parameterised queries throughout. |
| **Broken access control (A01)** | WebSocket subscriptions are bound to a known session id. Connecting to an unknown or expired (>60 min) id closes with code 4404. |
| **Security misconfiguration (A05)** | CORS is locked to an explicit allow-list (`ALLOWED_ORIGINS` env). Production defaults are the Vercel deployment + localhost only. |
| **Security headers** | `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, and a strict CSP (`default-src 'none'; frame-ancestors 'none'`) on every response. |
| **Rate limiting / DoS** | `slowapi` per-IP: 5 research runs / 15 min, 60 reads / min. 429 returned with retry-after. |
| **Secrets in logs (A09)** | API keys read from env via `pydantic-settings`. Startup fails fast if `GEMINI_API_KEY` or `TAVILY_API_KEY` look like placeholders. |
| **Vulnerable / outdated deps (A06)** | All deps pinned with lower bounds; dependabot welcome via repo Settings. |
| **XSS in PDF / report** | Sections render through React (auto-escapes). PDF goes through `markdown-it-py` with HTML disabled, then a fixed CSS — no raw user HTML reaches WeasyPrint. |
| **SSRF** | Outbound HTTP is constrained to Tavily + Gemini SDK calls; the agents themselves do not fetch arbitrary user-controlled URLs at runtime. |

## What is NOT mitigated (and why)

- **Authentication / accounts**: out of scope for a public demo. Anyone
  with the URL can run a research session.
- **Persistent abuse detection**: rate limiter is in-memory per process.
  An attacker rotating IPs would not be tracked across them. Sufficient
  for a free-tier demo; not sufficient for production.
- **Prompt injection of the LLM**: the Researcher agent fetches third-
  party web content via Tavily and feeds it to Gemini. A malicious page
  could try to steer the model. The Writer prompt is structurally
  constrained (strict markdown only) which limits how far a hostile
  injection can propagate to the rendered UI, but it does not eliminate
  the class.
- **DB durability / integrity**: SQLite on a free HF Space lives at
  `/tmp` and is wiped on container restart. History loss is a known
  behaviour, not a vulnerability.

## Supported versions

Only the `main` branch (and the running HuggingFace Space + Vercel
deployment) is supported. There are no released versions yet.
