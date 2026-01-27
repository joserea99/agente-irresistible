from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..services.magic_service import MagicService

from ..services.rag_service import RAGManager

router = APIRouter()
magic_service = MagicService()
rag_manager = RAGManager()

class MagicRequest(BaseModel):
    document_source: str
    action_type: str # "guide", "plan", "social"

@router.post("/generate")
async def generate_magic_content(request: MagicRequest):
    """
    Generates content based on the action type using content from the brain.
    """
    if not request.document_source:
        raise HTTPException(status_code=400, detail="Document source is required")

    # Fetch full content from RAG
    content = rag_manager.get_full_document(request.document_source)
    
    if not content:
        # Fallback: Maybe they passed the text directly? (Backward compatibility if needed, but let's stick to source for now)
        raise HTTPException(status_code=404, detail="Document content not found in Knowledge Base")

    result = ""
    
    if request.action_type == "guide":
        result = magic_service.generate_small_group_guide(content)
    elif request.action_type == "plan":
        result = magic_service.generate_implementation_plan(content)
    elif request.action_type == "social":
        result = magic_service.generate_social_media_posts(content)
    else:
        raise HTTPException(status_code=400, detail="Invalid action type. Must be 'guide', 'plan', or 'social'")
    
    return {"result": result}
