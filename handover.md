# Handover — TenantPilot

> This file reflects CURRENT status only (overwrite each update, don't append).

## Terminal / Python Notes

- Antigravity IDE uses PowerShell internally — prefix ALL commands with `cmd /c`.
- For git commits use hyphenated messages: `cmd /c "git commit -m my-message"`
- Python 3.14 is the default. Python 3.11 available via `py -3.11` if needed.

## Done

- Phase 1: Implementation Plan — `agent.md`
- Phase 2: DB schema + models + FastAPI skeleton
- Phase 3: WhatsApp Cloud API helpers
- Phase 4: LangGraph agent — 4-node pipeline
- Phase 5: Webhook + Dashboard REST API
- Phase 6: React dashboard frontend (Codex scaffold + Opus fixes)
- Phase 7: Dockerfile (multi-stage) + docker-compose.yml (3-service)
- Phase 9: README.md with screenshots, architecture diagram, full docs

## In Progress

- None.

## Next Step

- **Phase 10: Final cleanup/refactor** — if desired
- Or: test end-to-end with real MongoDB + NVIDIA key

## How to Run Locally

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
python -m scripts.seed_tenants

# Frontend
cd frontend && npm install && npm run dev

# Docker (everything)
docker compose up -d
docker compose exec backend python -m scripts.seed_tenants
```

## Model/Editor History

| Phase | Model | Status |
|-------|-------|--------|
| 1 | Claude Opus 4.6 | ✅ |
| 2 | Claude Sonnet 4.6 | ✅ |
| 3 | GPT-5.5 (Zed) | ✅ |
| 4 | Claude Opus 4.6 | ✅ |
| 5 | Claude Opus 4.6 | ✅ |
| 6 | Codex + Claude Opus 4.6 | ✅ |
| 7 | Claude Opus 4.6 | ✅ |
| 9 | Claude Opus 4.6 | ✅ |
