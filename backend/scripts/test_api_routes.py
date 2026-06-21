"""Smoke test for Phase 5 — webhook and dashboard API imports."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Test webhook router imports
from app.api.webhook import router as webhook_router
from app.api.webhook import verify_webhook, handle_inbound
print("OK: webhook router imported with %d routes" % len(webhook_router.routes))

# Test dashboard router imports
from app.api.dashboard import router as dashboard_router
from app.api.dashboard import (
    list_tenants, get_tenant, list_sessions,
    get_session_messages, send_broadcast,
    TenantResponse, SessionResponse, MessageResponse,
    BroadcastRequest, BroadcastResponse,
)
print("OK: dashboard router imported with %d routes" % len(dashboard_router.routes))

# Test response schemas
req = BroadcastRequest(
    tenant_id="luxury-furniture",
    customer_phone="+919876543210",
    text="Hello from the dashboard!",
)
print("OK: BroadcastRequest schema valid: %s" % req.model_dump())

resp = BroadcastResponse(status="sent", message_id="wamid.xxx")
print("OK: BroadcastResponse schema valid: %s" % resp.model_dump())

# Test that main.py can be imported and generates correct OpenAPI schema
from app.main import app

# OpenAPI schema contains all routes correctly, even from included routers
schema = app.openapi()
paths = list(schema.get("paths", {}).keys())
print("OK: OpenAPI paths: %s" % sorted(paths))

assert "/health" in paths, "Missing /health"
assert "/api/webhook" in paths, "Missing /api/webhook"
assert "/api/tenants" in paths, "Missing /api/tenants"
assert "/api/tenants/{tenant_id}" in paths, "Missing /api/tenants/{tenant_id}"
assert "/api/sessions" in paths, "Missing /api/sessions"
assert "/api/sessions/{session_id}/messages" in paths, "Missing /api/sessions/{session_id}/messages"
assert "/api/broadcast" in paths, "Missing /api/broadcast"
print("OK: All 7 expected API paths found in OpenAPI schema")

print("")
print("All Phase 5 smoke tests passed.")
