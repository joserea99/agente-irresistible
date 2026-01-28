
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
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

def process_and_index_file(file_path: str, filename: str, content_type: str):
    """Background task to process file and index to RAG"""
    try:
        rag = RAGManager()
        text_content = ""
        
        print(f"🔄 Processing file: {filename} ({content_type})")
        
        # 1. Extract Text
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
                 # We assume MediaService can handle the file path
                 print(f"🎙️ Transcribing {filename}...")
                 transcript = media_service.transcribe_media(file_path, mime_type=content_type)
                 text_content = f"--- TRANSCRIPT OF {filename} ---\n{transcript}"
             except Exception as e:
                 print(f"❌ Error transcribing {filename}: {e}")
                 return
        else:
            print(f"⚠️ Unsupported file type for auto-indexing: {content_type}")
            return

        # 2. Index to RAG
        if text_content.strip():
            # Use file:// pseudo-protocol for source
            source = f"file://{filename}"
            if rag.add_document(text_content, source, title=filename):
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
    file: UploadFile = File(...)
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
