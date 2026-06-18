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
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_temperature: float = 0.7

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
