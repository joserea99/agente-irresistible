"""
Tests for centralized configuration.
"""

import os


def test_settings_loads_defaults():
    """Settings should load with defaults when env vars are missing."""
    from app.core.config import Settings

    s = Settings(google_api_key="", supabase_url="", supabase_service_role_key="")
    assert s.gemini_model == "gemini-2.5-flash"
    assert s.gemini_embedding_model == "gemini-embedding-001"
    assert s.trial_days == 15


def test_cors_origins_parsing():
    """CORS origins should be parsed from comma-separated string."""
    from app.core.config import Settings

    s = Settings(allowed_origins="http://a.com, http://b.com , http://c.com")
    assert s.cors_origins == ["http://a.com", "http://b.com", "http://c.com"]


def test_cors_single_origin():
    """Single origin should work correctly."""
    from app.core.config import Settings

    s = Settings(allowed_origins="http://localhost:3000")
    assert s.cors_origins == ["http://localhost:3000"]
