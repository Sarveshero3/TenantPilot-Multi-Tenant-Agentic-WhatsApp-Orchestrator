# Handover — TenantPilot

> This file reflects CURRENT status only (overwrite each update, don't append).

## Terminal / Python Notes

- This session is running in **Zed**, so the old Antigravity-only `cmd /c` workaround is not required here.
- For backend commands, prefer Python 3.11 explicitly:
  ```
  py -3.11 -m compileall backend/app
  ```
- Default `python` currently resolves to Python 3.14. Python 3.11 is available at `py -3.11`.
- If dependency isolation is needed later, it is safe to create a local 3.11 venv with:
  ```
  py -3.11 -m venv .venv
  ```

## Done

- Phase 1: Implementation Plan written in `agent.md` (Claude Opus 4.6)
- Phase 2: DB schema + models + FastAPI skeleton (Claude Sonnet 4.6)
  - `backend/app/config.py` — pydantic-settings, all env vars
  - `backend/app/db.py` — Motor/Beanie init/close
  - `backend/app/models/tenant.py` — Tenant + MediaItem document
  - `backend/app/models/chat_session.py` — ChatSession + SessionStatus
  - `backend/app/models/message_log.py` — MessageLog + enums + 4 indexes
  - `backend/app/models/__init__.py` — clean public exports
  - `backend/app/main.py` — FastAPI skeleton with lifespan, CORS, health endpoint
  - `backend/scripts/seed_tenants.py` — upserts Tenant A + Tenant B with media libraries
  - `backend/requirements.txt` — dependency minimums
  - `.env.example` — all env vars documented
  - `.gitignore` — comprehensive
- Phase 3: WhatsApp Cloud API helpers (GPT-5.5)
  - `backend/app/whatsapp/client_interface.py` — `WhatsAppClient` protocol and shared `WhatsAppPayloadBuilder`
  - `backend/app/whatsapp/real_client.py` — `httpx.AsyncClient` Meta Graph API POST implementation
  - `backend/app/whatsapp/mock_client.py` — logs/returns exact outbound method, endpoint, headers, JSON payload
  - `backend/app/whatsapp/__init__.py` — `get_whatsapp_client()` factory, mock default, real mode with access token

## In Progress

- None.

## Next Step (exact)

- **HANDOFF REQUIRED** — switch to Phase 4: **Claude Opus 4.6 (Thinking)** for LangGraph graph + 4 nodes (Task 3):
  - `backend/app/agent/state.py` — `AgentState` TypedDict
  - `backend/app/agent/nodes/acknowledge.py` — mark inbound as read, typing on, session upsert, inbound log
  - `backend/app/agent/nodes/context_retriever.py` — tenant prompt/media + last 5 messages
  - `backend/app/agent/nodes/llm_reasoning.py` — NVIDIA LLM reasoning and media decision/tooling
  - `backend/app/agent/nodes/dispatcher.py` — send text/image/document, typing off, outbound log, session update
  - `backend/app/agent/graph.py` — linear graph: acknowledge → context_retriever → llm_reasoning → dispatcher → END

## Known Broken / Blocked

- No Phase 3 blockers known.
- Meta WhatsApp Business sandbox approval/status is still unknown.
- The webhook route, LangGraph nodes, dashboard API, and frontend are not implemented yet by design.
- Frontend deployment target is an **open decision** — do NOT pick a platform until asking the human.

## Validation Run

- `py -3.11 -m compileall backend/app` — passed.
- `py -3.11 -c "... get_whatsapp_client ..."` — factory returns `MockWhatsAppClient` in current/default config.
- `py -3.11 -c "... MockWhatsAppClient smoke test ..."` — exercised mark-as-read, typing on/off, text markdown pass-through, image, and document payloads; passed.
- `py -3.11 -c "... RealWhatsAppClient import ..."` — real client imports and payload builder works; passed.

## How to Run Locally Right Now

```
# 1. Set up .env (copy from .env.example, fill MONGODB_URI + NVIDIA_API_KEY)
cd backend
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn app.main:app --reload --port 8000
# Visit: http://localhost:8000/health  →  {"status": "ok", "env": "development"}

# 2. Seed demo tenants (requires MONGODB_URI set in .env)
py -3.11 -m scripts.seed_tenants
```

## WhatsApp Mode

**Mock mode is currently active by default** (`WHATSAPP_MODE=mock`).

- Mock mode does not require Meta credentials.
- If `WHATSAPP_PHONE_NUMBER_ID` is missing, mock requests use `<PHONE_NUMBER_ID>` in the logged endpoint.
- If `WHATSAPP_ACCESS_TOKEN` is missing, mock requests use `Bearer <WHATSAPP_ACCESS_TOKEN>` in the logged headers.
- Real mode requires `WHATSAPP_MODE=real` and `WHATSAPP_ACCESS_TOKEN`; per-tenant phone IDs can be passed into helper calls.

## Tunnel URL (for Meta webhook verification)

Not set yet — generate with `ngrok http 8000` when testing webhooks. Update this file with the URL each session.

## Model/Editor That Did This Work

- Phase 1: **Claude Opus 4.6 (Thinking)** — Implementation Plan
- Phase 2: **Claude Sonnet 4.6 (Thinking)** — DB schema + models + FastAPI skeleton
- Phase 3: **GPT-5.5 in Zed** — WhatsApp Cloud API helpers
