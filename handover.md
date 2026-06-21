# Handover — TenantPilot

> This file reflects CURRENT status only (overwrite each update, don't append).

## Terminal / Python Notes

- Antigravity IDE uses PowerShell internally — prefix ALL commands with `cmd /c`.
- For git commits use hyphenated messages: `cmd /c "git commit -m my-message"`
- Python 3.14 is the default. Python 3.11 available via `py -3.11` if needed.

## Done

- Phase 1–10: All implementation complete (see agent.md for details)
- MongoDB Atlas connected and seeded (cluster0.y4ydc1i.mongodb.net)
- Beanie 2.x migration (pymongo.AsyncMongoClient instead of motor)
- Config fix: .env path resolved from project root, not CWD
- Tenant A phone_number_id updated to real Meta ID (1202145532976125)
- WHATSAPP_MODE switched to "real"
- ngrok tunnel active: https://4eaf-103-79-170-186.ngrok-free.app
- Webhook verified with Meta

## In Progress

- Live WhatsApp testing (8 test messages) — awaiting Test #1

## Next Step

- User sends Test #1 from phone (+919315860035) to the WhatsApp Business number
- Watch backend logs for webhook POST + agent pipeline
- Watch dashboard for session appearing under luxury-furniture tenant
- Log results to evals.md

## Running Services

- Backend: `py -3.11 -m uvicorn app.main:app --port 8000` (task-936)
- Frontend: `npm run dev` on port 5173 (task-769)
- ngrok: `ngrok http 8000` (task-884)
