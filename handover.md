# Handover — TenantPilot

> This file reflects CURRENT status only (overwrite each update, don't append).

## Terminal / Python Notes

- Antigravity IDE uses PowerShell internally — prefix ALL commands with `cmd /c`.
- For git commits use hyphenated messages: `cmd /c "git commit -m my-message"`
- Python 3.14 is the default. Python 3.11 available via `py -3.11` if needed.
- See `lessons.md` L-002, L-003, L-004 for details.

## Done

- Phase 1: Implementation Plan written in `agent.md` (Claude Opus 4.6)
- Phase 2: DB schema + models + FastAPI skeleton (Claude Sonnet 4.6)
  - `backend/app/config.py`, `backend/app/db.py`, `backend/app/models/*`, `backend/app/main.py`
  - `backend/scripts/seed_tenants.py`, `backend/requirements.txt`, `.env.example`, `.gitignore`
- Phase 3: WhatsApp Cloud API helpers (GPT-5.5)
  - `backend/app/whatsapp/client_interface.py` — `WhatsAppClient` protocol + `WhatsAppPayloadBuilder`
  - `backend/app/whatsapp/real_client.py` — httpx-based real Meta Graph API client
  - `backend/app/whatsapp/mock_client.py` — logs exact JSON payloads
  - `backend/app/whatsapp/__init__.py` — `get_whatsapp_client()` factory
- Phase 4: LangGraph agent — 4-node pipeline (Claude Opus 4.6)
  - `backend/app/agent/state.py` — `AgentState` TypedDict (14 fields, total=False for partial updates)
  - `backend/app/agent/nodes/acknowledge.py` — mark read, typing ON, session upsert, inbound log
  - `backend/app/agent/nodes/context_retriever.py` — load tenant config + last 5 messages
  - `backend/app/agent/nodes/llm_reasoning.py` — NVIDIA Nemotron LLM with send_media tool-calling
  - `backend/app/agent/nodes/dispatcher.py` — send text/image/document, typing OFF, outbound log
  - `backend/app/agent/graph.py` — linear StateGraph: acknowledge -> context_retriever -> llm_reasoning -> dispatcher -> END
  - `backend/app/agent/__init__.py` — exports `agent_graph`, `AgentState`
  - `backend/app/agent/nodes/__init__.py` — exports all 4 node functions
  - `backend/scripts/test_agent_graph.py` — smoke test (all passed)

## In Progress

- None.

## Next Step (exact)

- **HANDOFF REQUIRED** — switch to Phase 5 (GPT-5.3-Codex or equivalent) for:
  - `backend/app/api/webhook.py` — GET verification + POST inbound handler with `BackgroundTasks`
  - `backend/app/api/dashboard.py` — REST API for frontend (tenants, sessions, messages, broadcast)
  - Update `backend/app/main.py` to mount the routers

## Known Broken / Blocked

- LangGraph pipeline requires MongoDB to be running for end-to-end test (nodes do DB reads/writes)
- NVIDIA_API_KEY needed in `.env` for real LLM calls; without it, LLM node returns a fallback text response
- Meta WhatsApp Business sandbox approval status unknown — mock mode default
- Frontend deployment target is an **open decision** — ask the human at Phase 7

## How to Run Locally Right Now

```
# 1. Set up .env (copy from .env.example, fill MONGODB_URI + NVIDIA_API_KEY)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Visit: http://localhost:8000/health

# 2. Seed demo tenants
python -m scripts.seed_tenants

# 3. Smoke test the agent graph (no DB/LLM needed)
python scripts/test_agent_graph.py
```

## WhatsApp Mode

**Mock mode** (`WHATSAPP_MODE=mock`) — no real Meta credentials needed.

## Tunnel URL

Not set yet — generate with `ngrok http 8000` when testing real webhooks.

## Model/Editor That Did This Work

- Phase 1: **Claude Opus 4.6 (Thinking)** — Implementation Plan
- Phase 2: **Claude Sonnet 4.6 (Thinking)** — DB schema + models + FastAPI skeleton
- Phase 3: **GPT-5.5 in Zed** — WhatsApp Cloud API helpers
- Phase 4: **Claude Opus 4.6 (Thinking)** — LangGraph agent (4 nodes + graph)
