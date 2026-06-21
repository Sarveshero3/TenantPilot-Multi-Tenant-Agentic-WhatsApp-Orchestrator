"""
Centralized configuration using pydantic-settings.
All env vars are read from here — never use os.getenv() directly elsewhere.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

# Project root is two levels up from this file (backend/app/config.py → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── MongoDB ──────────────────────────────────────────────────────────────
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI (Atlas or local)",
    )
    mongodb_db_name: str = Field(default="tenantpilot")

    # ── WhatsApp Cloud API ───────────────────────────────────────────────────
    whatsapp_mode: str = Field(
        default="mock",
        description="'mock' logs payloads; 'real' sends to Meta Graph API",
    )
    whatsapp_access_token: str = Field(
        default="",
        description="Meta Graph API bearer token",
    )
    whatsapp_phone_number_id: str = Field(
        default="",
        description="Default Meta phone number ID (overridden per tenant)",
    )
    whatsapp_api_version: str = Field(default="v20.0")
    whatsapp_verify_token: str = Field(
        default="tenantpilot_verify_secret",
        description="Shared secret for Meta webhook verification challenge",
    )
    whatsapp_app_secret: str = Field(
        default="",
        description="Meta App Secret key used to validate webhook signature (X-Hub-Signature-256)",
    )

    # ── LLM (NVIDIA AI Endpoints — free tier) ───────────────────────────────
    nvidia_api_key: str = Field(
        default="",
        description="NVIDIA AI Endpoints API key",
    )
    llm_model: str = Field(
        default="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    )
    llm_temperature: float = Field(default=0.6)
    llm_top_p: float = Field(default=0.95)
    llm_max_tokens: int = Field(default=65536)
    llm_reasoning_budget: int = Field(default=16384)

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    backend_port: int = Field(default=8000)
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Frontend origin for CORS",
    )
    log_level: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings instance (cached after first call)."""
    return Settings()
