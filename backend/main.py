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
# CORS Configuration
origins = [
    "http://localhost:3000",  # Next.js frontend local
]

# Robust CORS for Railway Subdomains
origin_regex = r"https://.*\.railway\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
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
from app.routers import auth, chat, brandfolder, magic, dojo, knowledge

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(brandfolder.router, prefix="/brandfolder", tags=["Brandfolder"])
app.include_router(magic.router, prefix="/magic", tags=["Magic"])
app.include_router(dojo.router, prefix="/dojo", tags=["Dojo"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
