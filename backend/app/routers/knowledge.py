import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
import shutil
import os
import uuid
from typing import List
from pydantic import BaseModel
import pypdf

from ..services.rag_service import RAGManager
from ..services.media_service import MediaService
from ..services.supabase_service import supabase_service
from ..services.auth_service import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "/app/brain_data/uploads" if os.path.exists("/app/brain_data") else "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

security = HTTPBearer()

class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str

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

        logger.info(f"Processing file: {filename} ({content_type})")

        # 1. Extract Text
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            try:
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Error reading PDF {filename}: {e}")
                return

        elif content_type in ["text/plain", "text/markdown"] or filename.lower().endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()

        elif content_type.startswith("audio/") or content_type.startswith("video/"):
            try:
                media_service = MediaService()
                logger.info(f"Transcribing {filename}...")
                transcript = media_service.transcribe_media(file_path, mime_type=content_type)
                text_content = f"--- TRANSCRIPT OF {filename} ---\n{transcript}"
            except Exception as e:
                logger.error(f"Error transcribing {filename}: {e}")
                return
        else:
            logger.warning(f"Unsupported file type for auto-indexing: {content_type}")
            return

        # 2. Upload to Supabase Storage (Archival)
        logger.info(f"Uploading {filename} to Supabase Storage...")
        public_url = ""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            bucket_name = "knowledge-base"
            storage_path = f"uploads/{filename}"

            public_url = supabase_service.upload_file(bucket_name, storage_path, file_bytes, content_type)
            if public_url:
                logger.info(f"Uploaded to: {public_url}")
            else:
                logger.warning("Upload failed, using filename as source.")
                public_url = f"file://{filename}"

        except Exception as e:
            logger.error(f"Error uploading to storage: {e}")
            public_url = f"file://{filename}"

        # 3. Index to RAG
        if text_content.strip():
            if rag.add_document(text_content, public_url, title=filename):
                logger.info(f"Successfully indexed {filename}")
            else:
                logger.info(f"Skipped {filename} (Already exists or empty)")
        else:
            logger.warning(f"No text extracted from {filename}")

    except Exception as e:
        logger.error(f"Critical Error processing {filename}: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Removed temp file {file_path}")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_current_admin)
):
    try:
        safe_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

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


@router.get("/documents")
async def list_documents(
    source_type: str = "all",
    limit: int = 100,
    admin_user: dict = Depends(get_current_admin)
):
    """
    List all documents in the knowledge base.
    source_type: 'all' | 'direct' (file://) | 'brandfolder' | 'web'
    """
    try:
        query = supabase_service.client.table("documents").select(
            "id, title, source, doc_type, created_at, updated_at"
        ).order("created_at", desc=True).limit(limit)

        if source_type == "direct":
            query = query.like("source", "file://%")
        elif source_type == "brandfolder":
            query = query.like("source", "%brandfolder.com%")
        elif source_type == "web":
            query = query.like("source", "http%").not_.like("source", "%brandfolder.com%")

        res = query.execute()

        # Add chunk count per document
        docs = res.data or []
        for doc in docs:
            try:
                chunks_res = supabase_service.client.table("document_chunks").select(
                    "id", count="exact", head=True
                ).eq("document_id", doc["id"]).execute()
                doc["chunk_count"] = chunks_res.count or 0
            except Exception:
                doc["chunk_count"] = 0

        return {"documents": docs, "total": len(docs)}

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    admin_user: dict = Depends(get_current_admin)
):
    """
    Delete a document and all its chunks from the knowledge base.
    """
    try:
        # 1. Delete all chunks first (foreign key)
        supabase_service.client.table("document_chunks").delete().eq(
            "document_id", document_id
        ).execute()

        # 2. Delete the document
        res = supabase_service.client.table("documents").delete().eq(
            "id", document_id
        ).execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info(f"Deleted document {document_id} and its chunks")
        return {"status": "deleted", "id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
