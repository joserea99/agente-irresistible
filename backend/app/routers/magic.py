import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.magic_service import MagicService
from ..services.rag_service import RAGManager

logger = logging.getLogger(__name__)

router = APIRouter()
magic_service = MagicService()
rag_manager = RAGManager()


class MagicRequest(BaseModel):
    document_source: Optional[str] = None
    content: Optional[str] = None
    action_type: str  # "sermon", "guide", "kids", "runsheet", "plan", "social"
    language: str = "es"


class SundayPackRequest(BaseModel):
    topic: str
    series_name: Optional[str] = None
    scripture: Optional[str] = None
    language: str = "es"


@router.post("/generate")
async def generate_magic_content(request: MagicRequest):
    """
    Generates a specific ministerial deliverable from either direct text/topic or a knowledge base document.
    """
    source_text = (request.content or "").strip()

    if not source_text and request.document_source:
        source_text = rag_manager.get_full_document(request.document_source) or ""
        if not source_text:
            # Fallback to using the document title/source name if full content is missing
            source_text = f"Recurso de referencia: {request.document_source}"

    if not source_text:
        raise HTTPException(status_code=400, detail="Se requiere un tema, texto o documento de origen.")

    action = request.action_type.lower()
    if action == "sermon":
        result = magic_service.generate_sermon_outline(source_text, request.language)
    elif action == "guide":
        result = magic_service.generate_small_group_guide(source_text, request.language)
    elif action == "kids":
        result = magic_service.generate_kids_lesson(source_text, request.language)
    elif action == "runsheet":
        result = magic_service.generate_service_runsheet(source_text, request.language)
    elif action == "plan":
        result = magic_service.generate_implementation_plan(source_text, request.language)
    elif action == "social":
        result = magic_service.generate_social_media_posts(source_text, request.language)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid action_type. Must be 'sermon', 'guide', 'kids', 'runsheet', 'plan', or 'social'.",
        )

    return {"result": result, "action_type": action}


@router.post("/sunday-pack")
async def generate_sunday_pack(request: SundayPackRequest):
    """
    Generates the complete 5-piece Sunday Production Pack in one click (parallel execution).
    """
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Por favor ingresa el tema, idea o pasaje de tu domingo.")

    pack = magic_service.generate_sunday_pack(
        topic=topic,
        series_name=request.series_name,
        scripture=request.scripture,
        language=request.language,
    )
    return {
        "topic": topic,
        "series_name": request.series_name,
        "scripture": request.scripture,
        "pack": pack,
    }
