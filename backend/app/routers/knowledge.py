
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
import shutil
import os
import uuid
from typing import List
from pydantic import BaseModel
import pypdf

# Services
from ..services.rag_service import RAGManager
from ..services.media_service import MediaService

router = APIRouter()

UPLOAD_DIR = "/app/brain_data/uploads" if os.path.exists("/app/brain_data") else "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str

    message: str

from ..services.supabase_service import supabase_service
from ..services.auth_service import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    profile, error = verify_token(token)
    
    if error != "success" or not profile:
         raise HTTPException(status_code=401, detail="Invalid token")
    
    if profile.get("role") != "admin":
         raise HTTPException(status_code=403, detail="Admin access required")
         
    return profile

def process_and_index_file(file_path: str, filename: str, content_type: str):
    """Background task to process file, upload to Cloud Storage, and index to RAG"""
    try:
        rag = RAGManager()
        text_content = ""
        
        print(f"🔄 Processing file: {filename} ({content_type})")
        
        # 1. Extract Text (Keep existing logic for extraction)
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            try:
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception as e:
                print(f"❌ Error reading PDF {filename}: {e}")
                return
                
        elif content_type in ["text/plain", "text/markdown"] or filename.lower().endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
                
        elif content_type.startswith("audio/") or content_type.startswith("video/"):
             # Use MediaService for transcription
             try:
                 media_service = MediaService()
                 print(f"🎙️ Transcribing {filename}...")
                 transcript = media_service.transcribe_media(file_path, mime_type=content_type)
                 text_content = f"--- TRANSCRIPT OF {filename} ---\n{transcript}"
             except Exception as e:
                 print(f"❌ Error transcribing {filename}: {e}")
                 return
        else:
            print(f"⚠️ Unsupported file type for auto-indexing: {content_type}")
            return

        # 2. Upload to Supabase Storage (Archival)
        print(f"☁️ Uploading {filename} to Supabase Storage...")
        public_url = ""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
                
            # Use 'knowledge-base' bucket
            bucket_name = "knowledge-base" 
            storage_path = f"uploads/{filename}"
            
            public_url = supabase_service.upload_file(bucket_name, storage_path, file_bytes, content_type)
            if public_url:
                print(f"✅ Uploaded to: {public_url}")
            else:
                 print("⚠️ Upload failed, using filename as source.")
                 public_url = f"file://{filename}"
                 
        except Exception as e:
            print(f"❌ Error uploading to storage: {e}")
            public_url = f"file://{filename}"

        # 3. Index to RAG using Cloud URL as Source
        if text_content.strip():
            if rag.add_document(text_content, public_url, title=filename):
                print(f"✅ Successfully indexed {filename}")
            else:
                print(f"⚠️ Skipped {filename} (Already exists or empty)")
        else:
            print(f"⚠️ No text extracted from {filename}")
            
    except Exception as e:
        print(f"❌ Critical Error processing {filename}: {e}")
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Removed temp file {file_path}")

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_current_admin)
):
    try:
        # Safe filename
        safe_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Queue background processing
        background_tasks.add_task(
            process_and_index_file, 
            file_path, 
            file.filename, 
            file.content_type
        )
        
        return {
            "filename": file.filename,
            "status": "queued",
            "message": "File uploaded and queued for processing."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
