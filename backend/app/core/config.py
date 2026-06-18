"""
Centralized configuration using Pydantic BaseSettings.
All environment variables and constants in one place.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- API Keys ---
    google_api_key: str = ""
    brandfolder_api_key: str = ""

    # --- Supabase ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # --- Planning Center OAuth2 ---
    planning_center_client_id: str = ""
    planning_center_client_secret: str = ""
    planning_center_redirect_uri: str = "http://localhost:8000/oauth/planning-center/callback"

    # --- Stripe ---
    stripe_secret_key: str = ""
    stripe_price_id: str = ""
    stripe_webhook_secret: str = ""

    # --- Auth ---
    secret_key: str = "change-me-in-production"
    trial_days: int = 15

    # --- CORS ---
    allowed_origins: str = "http://localhost:3000"

    # --- AI Model ---
    gemini_model: str = "gemini-2.5-flash"            # Default chat model
    gemini_model_heavy: str = "gemini-2.5-pro"        # For deep tasks (synthesis, deep research)
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_temperature: float = 0.7

    # --- Agent behavior ---
    # Thinking budget: -1 = dynamic (model decides), 0 = off, >0 = fixed token budget.
    gemini_thinking_budget: int = -1
    agent_tools_enabled: bool = True                  # Let the chat agent call tools (RAG search, browse, YouTube)
    agent_max_tool_calls: int = 5                     # Max tool-call rounds per response (agentic loop)

    # --- Rate Limiting ---
    rate_limit_chat: str = "30/minute"
    rate_limit_magic: str = "10/minute"
    rate_limit_default: str = "60/minute"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
