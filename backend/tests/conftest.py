"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
from unittest.mock import MagicMock

# Set test environment variables before any app imports
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("STRIPE_PRICE_ID", "price_test_fake")


@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock Supabase client for unit tests."""
    mock_client = MagicMock()
    monkeypatch.setattr(
        "app.services.supabase_service.supabase_service.client",
        mock_client,
    )
    return mock_client


@pytest.fixture
def mock_gemini(monkeypatch):
    """Mock Gemini client for unit tests."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Test AI response"
    mock_client.models.generate_content.return_value = mock_response
    return mock_client
