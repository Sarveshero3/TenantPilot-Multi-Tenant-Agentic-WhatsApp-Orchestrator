# Agent Architecture Record — TenantPilot

> Multi-Tenant WhatsApp Agentic Orchestrator

---

## 1. Stack Decisions

### Database: MongoDB (Atlas M0 Free Tier)

**Why MongoDB over Postgres:**
- The assignment explicitly names MongoDB Atlas M0 as its free-tier option, and Postgres requires Cloud SQL which isn't free.
- Message audit logs are naturally document-shaped (variable media attachments, context vars).
- Tenant media libraries are key-value maps (`"catalog" → "https://..."`) — native in BSON, awkward in relational.
- Schema flexibility helps during rapid prototyping within a 48-hour window.
- `motor` (async MongoDB driver) pairs perfectly with FastAPI's async model.

**ODM:** `beanie` (async ODM built on `motor` and Pydantic v2) — gives us Pydantic models for validation + MongoDB storage in one layer.

### Backend: Python 3.11+ / FastAPI

- LangGraph's primary SDK is Python.
- FastAPI's async + BackgroundTasks solves the "return 200 in <3s" webhook requirement natively.
- Pydantic v2 for request/response validation.

### AI Orchestration: LangGraph (Python)

- Required by the assignment.
- 4-node stateful graph: Acknowledge → Context Retriever → LLM Reasoning → Dispatcher.

### LLM Provider: NVIDIA Nemotron-3-nano-omni-30b-a3b-reasoning (via NVIDIA AI Endpoints)

- **Free** — no API cost, critical for prototype budget.
- Multimodal (handles text + images natively) — covers the bonus inbound image parsing.
- Reasoning-capable with configurable `reasoning_budget`.
- Integrated via `langchain_nvidia_ai_endpoints.ChatNVIDIA` — native LangChain compatibility.
- Falls back gracefully if NVIDIA endpoint is down (log error, skip LLM step).

### Frontend: React + Vite + Tailwind CSS v4

- Lightweight, fast dev iteration.
- Tailwind for rapid styling matching the "clean design" criterion.
- No SSR needed — pure SPA hitting the FastAPI backend.

### Deployment: Docker → GCP Cloud Run (preferred)

- Single Dockerfile packaging backend.
- Frontend served as static build from the same container OR separate static hosting (open decision — ask the human at Task 6 time).

---

## 2. Implementation Plan

### Task 1: Multi-Tenant Database Design

**What:** Define MongoDB collections and Beanie document models for Tenant, ChatSession, and MessageLog.

**Collections & Schema:**

#### `tenants` collection
```python
class Tenant(Document):
    tenant_id: str              # Unique slug, e.g. "luxury-furniture"
    name: str                   # Display name, e.g. "Luxury Furniture Store"
    whatsapp_phone_number_id: str  # Meta phone number ID for this tenant
    system_prompt: str          # LLM system instructions for this brand
    media_library: dict[str, MediaItem]  # key → {url, type, filename, description}
    created_at: datetime
    updated_at: datetime

class MediaItem(BaseModel):
    url: str                    # Public URL to the asset
    media_type: str             # "image" | "document"
    filename: Optional[str]     # For documents, e.g. "catalog.pdf"
    description: str            # Human-readable, helps LLM decide when to use
```

#### `chat_sessions` collection
```python
class SessionStatus(str, Enum):
    WAITING_FOR_BOT = "WAITING_FOR_BOT"
    AGENT_RESPONDING = "AGENT_RESPONDING"
    RESOLVED = "RESOLVED"
    NEEDS_HUMAN = "NEEDS_HUMAN"        # Bonus: sentiment handover

class ChatSession(Document):
    tenant_id: str
    customer_phone: str         # E.164 format
    status: SessionStatus
    context_vars: dict          # Arbitrary context (e.g. last product viewed)
    is_typing: bool             # Tracks whether typing indicator is active
    created_at: datetime
    updated_at: datetime
```

#### `message_logs` collection
```python
class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"

class MessageLog(Document):
    session_id: str             # References ChatSession
    tenant_id: str
    customer_phone: str
    direction: MessageDirection
    sender: str                 # "customer" | "bot" | "system"
    message_type: MessageType
    text_content: Optional[str]
    media_url: Optional[str]
    media_mime_type: Optional[str]
    media_filename: Optional[str]
    whatsapp_message_id: Optional[str]  # Meta's message ID for tracking
    timestamp: datetime
```

**Files:**
- `backend/app/models/tenant.py`
- `backend/app/models/chat_session.py`
- `backend/app/models/message_log.py`
- `backend/app/models/__init__.py`
- `backend/app/db.py` — MongoDB connection init via motor + beanie

**Seed data:** A script `backend/scripts/seed_tenants.py` that inserts Tenant A (Luxury Furniture) and Tenant B (Automotive Care) with sample media libraries.

---

### Task 2: WhatsApp Cloud API Integration

**What:** A `WhatsAppClient` class behind an interface/protocol so it can be swapped between `RealWhatsAppClient` and `MockWhatsAppClient`.

**API calls implemented:**
1. **Mark as read** — `POST /v20.0/{phone_number_id}/messages` with `{"messaging_product": "whatsapp", "status": "read", "message_id": "<id>"}`
2. **Typing indicator ON** — `POST /v20.0/{phone_number_id}/messages` with `{"messaging_product": "whatsapp", "recipient_type": "individual", "to": "<phone>", "type": "typing_indicator", "typing_indicator": {"type": "text"}}`
3. **Typing indicator OFF** — same endpoint, `"typing_indicator": {"type": "stop"}`  *(Note: verify from Meta docs if "stop" is a valid type or if typing auto-expires — if so, just skip the OFF call)*
4. **Send text** — `POST /v20.0/{phone_number_id}/messages` with `{"messaging_product": "whatsapp", "to": "<phone>", "type": "text", "text": {"body": "<markdown text>"}}`
5. **Send image** — same endpoint with `{"type": "image", "image": {"link": "<url>"}}`
6. **Send document** — same endpoint with `{"type": "document", "document": {"link": "<url>", "filename": "<name>"}}`

**Mock mode:** `MockWhatsAppClient` implements the same interface but prints the exact JSON payload, headers, and endpoint to stdout/logger instead of making HTTP calls. This demonstrates Meta API mastery even without live credentials.

**Files:**
- `backend/app/whatsapp/client_interface.py` — Protocol/ABC
- `backend/app/whatsapp/real_client.py` — httpx-based real client
- `backend/app/whatsapp/mock_client.py` — logs payloads
- `backend/app/whatsapp/__init__.py` — factory function that returns mock or real based on env var `WHATSAPP_MODE=mock|real`

**Env vars needed:**
- `WHATSAPP_MODE` — `mock` or `real`
- `WHATSAPP_ACCESS_TOKEN` — Meta Graph API token
- `WHATSAPP_PHONE_NUMBER_ID` — default phone number ID (overridden per-tenant)
- `WHATSAPP_API_VERSION` — default `v20.0`

---

### Task 3: Agentic Orchestration with LangGraph

**What:** A LangGraph `StateGraph` with 4 nodes processing inbound WhatsApp messages.

**State Schema:**
```python
class AgentState(TypedDict):
    # Input
    inbound_message_id: str         # WhatsApp message ID
    customer_phone: str
    tenant_id: str
    message_text: str
    message_type: str               # "text" | "image" | etc.
    media_url: Optional[str]        # If inbound media

    # Populated by Acknowledge node
    session_id: str
    
    # Populated by Context Retriever
    system_prompt: str
    media_library: dict
    chat_history: list[dict]        # Last 5 messages
    
    # Populated by LLM Reasoning
    response_type: str              # "text" | "image" | "document"
    response_text: Optional[str]
    response_media_url: Optional[str]
    response_media_filename: Optional[str]
    
    # Metadata
    error: Optional[str]
```

**Nodes:**

1. **`acknowledge_node`**
   - Calls `whatsapp_client.mark_as_read(message_id)`
   - Calls `whatsapp_client.typing_on(phone, tenant_phone_id)`
   - Upserts `ChatSession` (find by tenant_id + phone, create if not exists) → status = `AGENT_RESPONDING`, is_typing = True
   - Saves inbound message to `MessageLog`
   - Returns state with `session_id`

2. **`context_retriever_node`**
   - Loads `Tenant` document by `tenant_id`
   - Loads last 5 `MessageLog` entries for this session
   - Returns state with `system_prompt`, `media_library`, `chat_history`

3. **`llm_reasoning_node`**
   - Builds messages array: system prompt + chat history + current user message
   - Defines tools: `send_media(media_key: str)` — looks up key in media_library
   - Calls LLM with tool-calling enabled
   - If LLM calls `send_media` tool → sets `response_type` to image/document based on media item type, populates URL
   - If LLM returns text → sets `response_type` = "text", `response_text` = LLM output
   - Returns updated state

4. **`dispatcher_node`**
   - Based on `response_type`:
     - "text" → `whatsapp_client.send_text(phone, text)`
     - "image" → `whatsapp_client.send_image(phone, url)`
     - "document" → `whatsapp_client.send_document(phone, url, filename)`
   - Calls `whatsapp_client.typing_off(phone, tenant_phone_id)`
   - Saves outbound message to `MessageLog`
   - Updates `ChatSession`: status = `WAITING_FOR_BOT`, is_typing = False
   - Returns final state

**Graph edges:** Linear: `acknowledge → context_retriever → llm_reasoning → dispatcher → END`

*(Bonus extension: conditional edge from llm_reasoning to a `human_handover` node if sentiment is negative.)*

**Files:**
- `backend/app/agent/state.py` — AgentState TypedDict
- `backend/app/agent/nodes/acknowledge.py`
- `backend/app/agent/nodes/context_retriever.py`
- `backend/app/agent/nodes/llm_reasoning.py`
- `backend/app/agent/nodes/dispatcher.py`
- `backend/app/agent/graph.py` — builds and compiles the StateGraph
- `backend/app/agent/__init__.py`

---

### Task 4: Async Webhook Handler

**What:** FastAPI endpoints for Meta WhatsApp webhook integration.

**Endpoints:**

1. **`GET /api/webhooks/whatsapp`** — Verification endpoint
   - Params: `hub.mode`, `hub.verify_token`, `hub.challenge`
   - Returns `hub.challenge` as plain text if token matches env var `WHATSAPP_VERIFY_TOKEN`

2. **`POST /api/webhooks/whatsapp`** — Inbound message handler
   - Parses Meta's webhook payload to extract message details
   - Returns `200 OK` immediately (within <3 seconds)
   - Kicks off LangGraph agent run via `BackgroundTasks.add_task()` or `asyncio.create_task()`
   - The background task: resolves tenant_id from the phone_number_id in the payload → invokes the compiled LangGraph graph with the initial state

3. **Dashboard API endpoints** (for Task 5):
   - `GET /api/tenants` — list all tenants
   - `GET /api/tenants/{tenant_id}/sessions` — list active chat sessions
   - `GET /api/tenants/{tenant_id}/sessions/{session_id}/messages` — get message history
   - `POST /api/broadcast` — trigger broadcast (stub for prototype)
   - `GET /api/tenants/{tenant_id}/sessions/{session_id}/stream` — SSE endpoint for live updates

**Files:**
- `backend/app/api/webhook.py` — GET + POST webhook endpoints
- `backend/app/api/dashboard.py` — dashboard REST endpoints
- `backend/app/api/__init__.py`
- `backend/app/main.py` — FastAPI app, CORS, lifespan (DB init), router mounting

---

### Task 5: Lightweight Frontend Dashboard

**What:** React SPA with tenant switching, live chat monitoring, and broadcast UI.

**Pages/Components:**

1. **Layout** — sidebar with tenant switcher + main content area
2. **TenantSwitcher** — dropdown/tabs showing all tenants, switches context
3. **ChatList** — list of active phone numbers for selected tenant, shows session status badges
4. **ChatThread** — stylized message thread:
   - User messages (left-aligned, different color)
   - Bot messages (right-aligned) with:
     - Text content
     - Image thumbnails with lightbox
     - Document badges (PDF icon + filename, clickable)
   - "Typing..." indicator when bot is thinking
   - Timestamps and metadata
5. **BroadcastDrawer** — slide-out panel:
   - Select cohort (all customers, specific numbers)
   - Pick template message
   - Send button (calls stub API)
6. **StatusBadge** — colored badges for session status (WAITING, RESPONDING, RESOLVED, NEEDS_HUMAN)

**Data flow:** Polling or SSE from backend for live updates. Start with polling (every 2s), upgrade to SSE if time allows.

**Files:**
- `frontend/` — Vite + React project
- `frontend/src/App.jsx`
- `frontend/src/components/Layout.jsx`
- `frontend/src/components/TenantSwitcher.jsx`
- `frontend/src/components/ChatList.jsx`
- `frontend/src/components/ChatThread.jsx`
- `frontend/src/components/BroadcastDrawer.jsx`
- `frontend/src/components/StatusBadge.jsx`
- `frontend/src/api/client.js` — axios/fetch wrapper
- `frontend/src/hooks/usePolling.js`

---

### Task 6: Cloud Deployment

**What:** Dockerize and deploy to GCP Cloud Run (or fallback).

**Approach:**
- Single `Dockerfile` (multi-stage):
  - Stage 1: Build frontend (`npm run build`)
  - Stage 2: Python backend with FastAPI serving the built frontend as static files
- `docker-compose.yml` for local development (backend + frontend dev servers + MongoDB)
- Cloud Run deployment via `gcloud run deploy`
- Env vars via Cloud Run env config or Secret Manager

**⚠️ OPEN DECISION:** Frontend deployment target (Cloud Run static container vs. Firebase Hosting vs. bundled in backend container) — **ask the human when reaching this task.**

**Files:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`

---

## 3. Folder Structure

```
TenantPilot-Multi-Tenant-Agentic-WhatsApp-Orchestrator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings via pydantic-settings
│   │   ├── db.py                   # MongoDB/Beanie init
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── chat_session.py
│   │   │   └── message_log.py
│   │   ├── whatsapp/
│   │   │   ├── __init__.py
│   │   │   ├── client_interface.py
│   │   │   ├── real_client.py
│   │   │   └── mock_client.py
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── state.py
│   │   │   ├── graph.py
│   │   │   └── nodes/
│   │   │       ├── __init__.py
│   │   │       ├── acknowledge.py
│   │   │       ├── context_retriever.py
│   │   │       ├── llm_reasoning.py
│   │   │       └── dispatcher.py
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── webhook.py
│   │       └── dashboard.py
│   ├── scripts/
│   │   └── seed_tenants.py
│   ├── tests/
│   │   └── ...
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── components/
│   │   │   ├── Layout.jsx
│   │   │   ├── TenantSwitcher.jsx
│   │   │   ├── ChatList.jsx
│   │   │   ├── ChatThread.jsx
│   │   │   ├── BroadcastDrawer.jsx
│   │   │   └── StatusBadge.jsx
│   │   └── hooks/
│   │       └── usePolling.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── .gitignore
├── agent.md
├── lessons.md
├── handover.md
└── README.md
```

---

## 4. Environment Variables

```env
# MongoDB
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/tenantpilot?retryWrites=true&w=majority
MONGODB_DB_NAME=tenantpilot

# WhatsApp
WHATSAPP_MODE=mock                          # mock | real
WHATSAPP_ACCESS_TOKEN=<meta-graph-api-token>
WHATSAPP_PHONE_NUMBER_ID=<default-phone-id>
WHATSAPP_API_VERSION=v20.0
WHATSAPP_VERIFY_TOKEN=<random-string-for-webhook-verification>

# LLM (NVIDIA AI Endpoints — free tier)
NVIDIA_API_KEY=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
LLM_MODEL=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning

# App
APP_ENV=development
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173           # For CORS
LOG_LEVEL=INFO
```

---

## 5. Iteration Plan (Mapping to Assignment Tasks)

### Iteration 1 (Phase 2 + Phase 3)
- **Task 1:** MongoDB schema + Beanie models + seed script → **Phase 2: Claude Sonnet 4.6**
- **Task 2:** WhatsApp client interface + mock + real → **Phase 3: GPT-5.3-Codex**
- Skeleton FastAPI app (`main.py`, `config.py`, `db.py`)

### Iteration 2 (Phase 4 + Phase 5)
- **Task 3:** LangGraph graph, all 4 nodes → **Phase 4: Claude Opus 4.6**
- **Task 4:** Async webhook handler + dashboard API → **Phase 5: GPT-5.3-Codex**
- **End-to-end test:** curl to webhook → agent processes → message logged → API returns it

### Iteration 3 (Phase 6)
- **Task 5:** React dashboard → **Phase 6: GPT-5.3-Codex**
- Wire real Meta credentials if available (or keep mock mode)
- Basic Dockerfile

### Iteration 4+ (Phase 7+)
- **Task 6:** Docker + Cloud Run → **Phase 7: Gemini 3.1 Pro**
- README + docs → **Phase 9: Gemini 3.5 Flash**
- Final cleanup → **Phase 10: Claude Sonnet 4.6**

---

## 6. Model Handoff Map

| Phase | Task | Assigned Model | Status |
|-------|------|----------------|--------|
| 1 | Read PDF + Implementation Plan | Claude Opus 4.6 (Thinking) | ✅ COMPLETE |
| 2 | DB schema + models (Task 1) | Claude Sonnet 4.6 (Thinking) | ✅ COMPLETE |
| 3 | WhatsApp Cloud API helpers (Task 2) | GPT-5.3-Codex | ⬜ NOT STARTED |
| 4 | LangGraph graph + 4 nodes (Task 3) | Claude Opus 4.6 (Thinking) | ⬜ NOT STARTED |
| 5 | Async webhook handler (Task 4) | GPT-5.3-Codex | ⬜ NOT STARTED |
| 6 | React dashboard (Task 5) | GPT-5.3-Codex | ⬜ NOT STARTED |
| 7 | Dockerfile + Cloud Run (Task 6) | Gemini 3.1 Pro (High) | ⬜ NOT STARTED |
| 8 | Debugging (any phase) | Gemini 3.5 Flash → Sonnet → Opus | ⬜ AS NEEDED |
| 9 | README + docs | Gemini 3.5 Flash (High) | ⬜ NOT STARTED |
| 10 | Final cleanup/refactor | Claude Sonnet 4.6 (Thinking) | ⬜ NOT STARTED |

---

## 7. Key Architectural Decisions (ADRs)

### ADR-001: MongoDB over PostgreSQL
- **Context:** Assignment allows either. Need fast iteration in 48h window.
- **Decision:** MongoDB Atlas M0 (free tier), accessed via `motor` + `beanie`.
- **Rationale:** Document shape matches data model (variable media, nested context vars). Free tier readily available. No ORM migration overhead.

### ADR-002: Beanie ODM over raw Motor
- **Context:** Need Pydantic validation + MongoDB persistence.
- **Decision:** Use Beanie (async ODM on top of motor).
- **Rationale:** Single model definition serves as both Pydantic schema and MongoDB document. Reduces boilerplate significantly.

### ADR-003: WhatsApp client behind Protocol/ABC
- **Context:** Meta sandbox approval may not arrive in time.
- **Decision:** Program against an interface. Factory function returns mock or real based on env var.
- **Rationale:** Allows full end-to-end development and demonstration without live credentials. Mock client logs exact payloads to prove API mastery.

### ADR-004: BackgroundTasks for async webhook processing
- **Context:** Webhook must return 200 in <3s. LangGraph run takes 5-30s (LLM latency).
- **Decision:** Use FastAPI's `BackgroundTasks` (or `asyncio.create_task()`) to kick off the graph run after returning 200.
- **Rationale:** Simplest approach. No external task queue (Celery/Redis) needed for prototype. If scaling, would migrate to a proper task queue.

### ADR-005: NVIDIA Nemotron-3-nano-omni-30b as default LLM
- **Context:** Need tool-calling support for media dispatch decisions. Budget constraint — prefer free models.
- **Decision:** NVIDIA Nemotron-3-nano-omni-30b-a3b-reasoning via `langchain_nvidia_ai_endpoints`.
- **Rationale:** Completely free API, multimodal (covers bonus image parsing), reasoning-capable with configurable budget, and has native LangChain integration via `ChatNVIDIA`. No API cost at all vs. GPT-4o-mini's per-token charges.
- **Integration pattern:**
  ```python
  from langchain_nvidia_ai_endpoints import ChatNVIDIA
  client = ChatNVIDIA(
      model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      api_key=os.getenv("NVIDIA_API_KEY"),
      temperature=0.6, top_p=0.95,
      max_tokens=65536, reasoning_budget=16384,
      chat_template_kwargs={"enable_thinking": True},
  )
  ```

### ADR-006: React + Vite + Tailwind for frontend
- **Context:** Need a "lightweight" dashboard per assignment spec.
- **Decision:** Vite for fast dev, React for component model, Tailwind for rapid styling.
- **Rationale:** No SSR needed. Pure SPA is simplest. Tailwind matches "clean design" criterion.

---

## 8. What Gets Mocked vs. Real (First Prototype)

| Component | Mock | Real | Notes |
|-----------|------|------|-------|
| WhatsApp API calls | ✅ MockWhatsAppClient logs payloads | Only if Meta approves sandbox | Toggle via `WHATSAPP_MODE` env var |
| MongoDB | — | ✅ Real MongoDB Atlas M0 | Free tier, always real |
| NVIDIA LLM | — | ✅ Real API calls (free tier) | Need `NVIDIA_API_KEY` in `.env` |
| Webhook inbound | ✅ curl/script simulates Meta payload | Real when Meta sandbox is wired | Use ngrok for HTTPS tunnel |
| Frontend data | — | ✅ Reads from real DB via API | Polling-based initially |
| Broadcast | ✅ Stub API, logs intent | — | UI exists, backend is a stub |
