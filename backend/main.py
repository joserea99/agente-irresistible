from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Irresistible Agent API",
    description="Backend API for the Irresistible Church Agent",
    version="2.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Next.js frontend local
    "https://web-production-7054f.up.railway.app", # Backend URL
    "https://frontend-production-c8fb.up.railway.app", # Frontend Production URL
    "https://www.irresistibleagent.com", # Custom Domain
    "https://irresistibleagent.com", # Custom Domain Root
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Irresistible Agent API v2.0 is running 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include Routers
from app.routers import auth, chat, brandfolder, magic, dojo, knowledge, sync

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(brandfolder.router, prefix="/brandfolder", tags=["Brandfolder"])
app.include_router(magic.router, prefix="/magic", tags=["Magic"])
app.include_router(dojo.router, prefix="/dojo", tags=["Dojo"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
app.include_router(sync.router, prefix="/sync", tags=["Auto Sync"])

# Subscription Router
from app.routers import subscription
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
        print("⚠️  [Scheduler] BRANDFOLDER_API_KEY not set. Auto-sync scheduler disabled.")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.services.sync_service import full_sync

        scheduler = BackgroundScheduler(
            job_defaults={"misfire_grace_time": 3600}  # Allow up to 1h late start
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
        print("✅ [Scheduler] Auto-sync scheduler started. Next run in 7 days.")
    except Exception as e:
        print(f"❌ [Scheduler] Failed to start scheduler: {e}")

