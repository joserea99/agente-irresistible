from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# --- Logging Setup ---
from app.core.logging import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# --- App Init ---
app = FastAPI(
    title="Irresistible Agent API",
    description="Backend API for the Irresistible Church Agent",
    version="2.1.0"
)

# --- Exception Handlers ---
from app.core.exceptions import register_exception_handlers
register_exception_handlers(app)

# --- CORS from environment ---
from app.core.config import settings

default_origins = [
    "http://localhost:3000",
    "https://web-production-7054f.up.railway.app",
    "https://frontend-production-c8fb.up.railway.app",
    "https://www.irresistibleagent.com",
    "https://irresistibleagent.com",
]

origins = settings.cors_origins if settings.allowed_origins != "http://localhost:3000" else default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiting ---
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled")
except ImportError:
    logger.warning("slowapi not installed — rate limiting disabled. Run: pip install slowapi")

# --- Routes ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "Irresistible Agent API v2.1 is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include Routers
from app.routers import auth, chat, brandfolder, magic, dojo, knowledge, sync, subscription

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(brandfolder.router, prefix="/brandfolder", tags=["Brandfolder"])
app.include_router(magic.router, prefix="/magic", tags=["Magic"])
app.include_router(dojo.router, prefix="/dojo", tags=["Dojo"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
app.include_router(sync.router, prefix="/sync", tags=["Auto Sync"])
app.include_router(subscription.router, prefix="/subscription", tags=["Subscription"])

# ---------- Automatic Scheduler ----------
@app.on_event("startup")
async def start_auto_sync_scheduler():
    """
    Starts the background scheduler that automatically syncs ALL Brandfolder
    content into the agent's memory every 7 days.
    Only activates if a Brandfolder API key is configured.
    """
    if not os.environ.get("BRANDFOLDER_API_KEY"):
        logger.info("BRANDFOLDER_API_KEY not set. Auto-sync scheduler disabled.")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.services.sync_service import full_sync

        scheduler = BackgroundScheduler(
            job_defaults={"misfire_grace_time": 3600}
        )
        scheduler.add_job(
            func=full_sync,
            trigger="interval",
            days=7,
            id="full_library_sync",
            name="Brandfolder Full Library Sync",
            replace_existing=True
        )
        scheduler.start()
        logger.info("Auto-sync scheduler started. Next run in 7 days.")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
