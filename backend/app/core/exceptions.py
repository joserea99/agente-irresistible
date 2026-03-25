"""
Custom exception classes and global FastAPI exception handlers.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# --- Custom Exceptions ---

class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ChatError(AppError):
    """Error in chat service."""
    def __init__(self, message: str = "Chat service error"):
        super().__init__(message, status_code=500)


class RAGError(AppError):
    """Error in RAG / knowledge base operations."""
    def __init__(self, message: str = "Knowledge base error"):
        super().__init__(message, status_code=500)


class SubscriptionError(AppError):
    """Error in subscription / payment operations."""
    def __init__(self, message: str = "Subscription error"):
        super().__init__(message, status_code=402)


class AuthError(AppError):
    """Error in authentication."""
    def __init__(self, message: str = "Authentication error"):
        super().__init__(message, status_code=401)


# --- Standard API Response ---

def api_response(data=None, error: str = None, status_code: int = 200):
    """Create a standardized API response."""
    body = {
        "success": error is None,
        "data": data,
        "error": error,
    }
    return JSONResponse(content=body, status_code=status_code)


# --- Global Exception Handlers ---

def register_exception_handlers(app: FastAPI):
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": "Internal server error",
            },
        )
