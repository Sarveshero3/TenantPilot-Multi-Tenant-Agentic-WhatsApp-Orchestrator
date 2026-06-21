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
- Phase 6: React dashboard frontend (Codex + Claude Opus 4.6)
  - Codex scaffolded all components, Claude fixed package.json/tsconfig/vite-env.d.ts
  - `frontend/src/types/index.ts` — TS interfaces matching backend API
  - `frontend/src/api/client.ts` — fetch wrapper with typed methods
  - `frontend/src/App.tsx` — 3-panel layout with polling (3s sessions, 2s messages)
  - `frontend/src/components/TenantSidebar.tsx` — tenant list with initials + status
  - `frontend/src/components/SessionList.tsx` — sessions with status badges, typing indicators, relative timestamps
  - `frontend/src/components/MessageThread.tsx` — chat bubbles (inbound/outbound), image/document rendering, auto-scroll
  - `frontend/src/components/BroadcastInput.tsx` — reply textarea → POST /api/broadcast
  - `frontend/src/components/StatusBadge.tsx` — color-coded session status
  - `frontend/src/components/TypingIndicator.tsx` — animated 3-dot indicator
  - All CSS files with dark theme, glassmorphism, shimmer loading skeletons, toast errors

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

- **Phase 7: Dockerfile + Docker Compose + deployment config**
  - Multi-stage Dockerfile for backend (Python) and frontend (Node → nginx)
  - `docker-compose.yml` for local dev (backend + mongo + frontend)
  - Cloud Run / Render deployment config
- **Phase 9: README + documentation**
  - Full setup guide, architecture diagram, demo screenshots

## Known Broken / Blocked

- Backend requires MongoDB to run (DB seed needed first)
- NVIDIA_API_KEY set in `.env` ✅
- Meta WhatsApp sandbox approval unknown — mock mode default
- Frontend shows "API offline" until backend is started
- Root-level `package-lock.json` (133 bytes, leftover from Codex) — harmless

## How to Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Seed tenants: python -m scripts.seed_tenants

# Frontend
cd frontend
npm install
npm run dev
# Visit: http://localhost:5173

# Backend Swagger: http://localhost:8000/docs
```

## Model/Editor That Did This Work

- Phase 1: **Claude Opus 4.6 (Thinking)** — Implementation Plan
- Phase 2: **Claude Sonnet 4.6 (Thinking)** — DB schema + models + FastAPI skeleton
- Phase 3: **GPT-5.5 in Zed** — WhatsApp Cloud API helpers
- Phase 4: **Claude Opus 4.6 (Thinking)** — LangGraph agent (4 nodes + graph)
- Phase 5: **Claude Opus 4.6 (Thinking)** — Webhook + Dashboard REST API
- Phase 6: **Codex** (scaffold) + **Claude Opus 4.6** (package fix, TS fix, verification)
