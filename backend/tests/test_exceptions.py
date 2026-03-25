"""
Tests for custom exceptions and API responses.
"""

from app.core.exceptions import AppError, ChatError, RAGError, SubscriptionError, AuthError, api_response


def test_app_error_defaults():
    err = AppError()
    assert err.status_code == 500
    assert err.message == "An unexpected error occurred"


def test_chat_error():
    err = ChatError("Model failed")
    assert err.status_code == 500
    assert err.message == "Model failed"


def test_rag_error():
    err = RAGError()
    assert err.status_code == 500


def test_subscription_error():
    err = SubscriptionError()
    assert err.status_code == 402


def test_auth_error():
    err = AuthError()
    assert err.status_code == 401


def test_api_response_success():
    resp = api_response(data={"key": "value"})
    body = resp.body
    assert b'"success": true' in body or b'"success":true' in body


def test_api_response_error():
    resp = api_response(error="Something failed", status_code=400)
    assert resp.status_code == 400
