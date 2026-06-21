# Handover — TenantPilot

> This file reflects CURRENT status only (overwrite each update, don't append).

## Terminal / Python Notes

- Antigravity IDE uses PowerShell internally — prefix ALL commands with `cmd /c`.
- For git commits use hyphenated messages: `cmd /c "git commit -m my-message"`
- Python 3.14 is the default. Python 3.11 available via `py -3.11` if needed.
- See `lessons.md` L-002, L-003, L-004 for details.

## Done

- Phase 1: Implementation Plan — `agent.md` (Claude Opus 4.6)
- Phase 2: DB schema + models + FastAPI skeleton (Claude Sonnet 4.6)
- Phase 3: WhatsApp Cloud API helpers (GPT-5.5)
- Phase 4: LangGraph agent — 4-node pipeline (Claude Opus 4.6)
- Phase 5: Webhook + Dashboard REST API (Claude Opus 4.6)
  - `backend/app/api/webhook.py` — GET verify (hub.verify_token) + POST inbound (BackgroundTasks → agent graph)
  - `backend/app/api/dashboard.py` — 5 endpoints: list/get tenants, list sessions, get messages, broadcast
  - `backend/app/api/__init__.py` — clean exports
  - `backend/app/main.py` — routers mounted at /api prefix
  - `backend/scripts/test_api_routes.py` — OpenAPI schema verification (all 7 paths confirmed)

## Full API Surface

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness probe |
| GET | `/api/webhook` | Meta verification challenge |
| POST | `/api/webhook` | Inbound WhatsApp message handler |
| GET | `/api/tenants` | List all tenants |
| GET | `/api/tenants/{tenant_id}` | Get one tenant |
| GET | `/api/sessions` | List sessions (?tenant_id= filter) |
| GET | `/api/sessions/{session_id}/messages` | Message history |
| POST | `/api/broadcast` | Send manual message |

## In Progress

- None.

## Next Step (exact)

- **HANDOFF REQUIRED** — switch to Phase 6 for **React dashboard frontend** (Task 5):
  - Use Vite + React + TypeScript
  - Tenant selector sidebar → Session list → Message thread view
  - Real-time typing indicators
  - Connect to dashboard REST API above
  - See `agent.md` Phase 6 for full spec

## Known Broken / Blocked

- Backend requires MongoDB to run (DB seed needed first)
- NVIDIA_API_KEY in `.env` for real LLM calls; without it, LLM node returns fallback text
- Meta WhatsApp sandbox approval unknown — mock mode default
- Frontend deployment target is an **open decision** — ask the human

## How to Run Locally

```
cd backend
pip install -r requirements.txt

# Set up .env (copy from .env.example, fill MONGODB_URI + NVIDIA_API_KEY)
uvicorn app.main:app --reload --port 8000

# Visit: http://localhost:8000/docs  → Full Swagger UI with all 7 endpoints
# Health: http://localhost:8000/health

# Seed demo tenants
python -m scripts.seed_tenants

# Run smoke tests (no DB/LLM required)
python scripts/test_imports.py
python scripts/test_agent_graph.py
python scripts/test_api_routes.py
```

## Model/Editor That Did This Work

- Phase 1: **Claude Opus 4.6 (Thinking)** — Implementation Plan
- Phase 2: **Claude Sonnet 4.6 (Thinking)** — DB schema + models + FastAPI skeleton
- Phase 3: **GPT-5.5 in Zed** — WhatsApp Cloud API helpers
- Phase 4: **Claude Opus 4.6 (Thinking)** — LangGraph agent (4 nodes + graph)
- Phase 5: **Claude Opus 4.6 (Thinking)** — Webhook + Dashboard REST API
