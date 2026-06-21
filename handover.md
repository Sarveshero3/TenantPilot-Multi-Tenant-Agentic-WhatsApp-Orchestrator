# Handover — TenantPilot

> This file reflects CURRENT status only (overwrite each update, don't append).

## ⚠️ CRITICAL: Terminal Commands

**Antigravity IDE uses PowerShell internally regardless of VS Code settings.**
Use `cmd /c` prefix for all commands. For git commits, use hyphenated messages (no spaces/quotes):
```
cmd /c "git add ."
cmd /c "git commit -m my-hyphenated-message"
```
See `lessons.md` L-002 for details.

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
  - `backend/requirements.txt` — pinned deps
  - `.env.example` — all env vars documented
  - `.gitignore` — comprehensive

## In Progress

- pip installing dependencies (task-140 background)

## Next Step (exact)

- **HANDOFF REQUIRED** — switch to Phase 3 (GPT-5.3-Codex) for WhatsApp Cloud API helpers (Task 2):
  - `backend/app/whatsapp/client_interface.py` — Protocol/ABC
  - `backend/app/whatsapp/real_client.py` — httpx-based Meta Graph API calls
  - `backend/app/whatsapp/mock_client.py` — logs exact JSON payloads
  - `backend/app/whatsapp/__init__.py` — factory: `get_whatsapp_client()` returns mock or real

## Known Broken / Blocked

- Pip install still in progress (task-140). Run `pip install -r requirements.txt` before any Python work.
- Models not yet smoke-tested (waiting for beanie to finish installing).
- WhatsApp clients not yet implemented — placeholder `__init__.py` only.
- Meta WhatsApp Business sandbox approval status unknown — mock mode default.
- Frontend deployment target is an **open decision** — do NOT pick a platform until asking the human.

## How to Run Locally Right Now

```
# 1. Set up .env (copy from .env.example, fill MONGODB_URI + NVIDIA_API_KEY)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Visit: http://localhost:8000/health  →  {"status": "ok", "env": "development"}

# 2. Seed demo tenants (requires MONGODB_URI set in .env)
python -m scripts.seed_tenants
```

## WhatsApp Mode

**Mock mode** (`WHATSAPP_MODE=mock`) — no real Meta credentials needed.

## Tunnel URL (for Meta webhook verification)

Not set yet — generate with `ngrok http 8000` when testing webhooks. Update this file with the URL each session.

## Model/Editor That Did This Work

- Phase 1: **Claude Opus 4.6 (Thinking)** — Implementation Plan
- Phase 2: **Claude Sonnet 4.6 (Thinking)** — DB schema + models + FastAPI skeleton
