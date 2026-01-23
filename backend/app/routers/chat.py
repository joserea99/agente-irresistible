from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from ..services.chat_service import ChatService
from ..services.auth_service import get_current_user
import os
from io import BytesIO

router = APIRouter()

# Pydantic Models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    director: str = "Programación de Servicio"
    rag_enabled: bool = False

class ChatResponse(BaseModel):
    message: str

class ExportRequest(BaseModel):
    history: List[Message]
    title: str = "Conversación"

# Initialize chat service
def get_chat_service():
    api_key = os.environ.get("GOOGLE_API_KEY")
    return ChatService(api_key=api_key)

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message and get AI response
    """
    try:
        # Convert Pydantic models to dicts
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        
        # Get RAG context if enabled (TODO: integrate RAG service)
        rag_context = None
        if request.rag_enabled:
            # TODO: Implement RAG search
            pass
        
        # Generate response
        response_text = chat_service.generate_response(
            user_input=request.message,
            history=history_dicts,
            director=request.director,
            rag_context=rag_context
        )
        
        return {"message": response_text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.get("/directors")
async def get_directors(chat_service: ChatService = Depends(get_chat_service)):
    """
    Get list of available directors
    """
    return {"directors": chat_service.get_directors()}

@router.post("/export")
async def export_conversation(
    request: ExportRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Export conversation to Word document
    """
    try:
        # Convert Pydantic models to dicts
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        
        # Generate document
        docx_bytes = chat_service.export_conversation_to_docx(
            history=history_dicts,
            title=request.title
        )
        
        # Return as downloadable file
        return StreamingResponse(
            BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={request.title}.docx"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting conversation: {str(e)}")

@router.get("/history/{user_id}")
async def get_chat_history(user_id: str):
    """
    Get chat history for a user (TODO: implement database storage)
    """
    # TODO: Implement database storage for chat history
    return {"history": [], "message": "Chat history storage not yet implemented"}

@router.post("/clear")
async def clear_chat_history(user_id: str):
    """
    Clear chat history for a user (TODO: implement database storage)
    """
    # TODO: Implement database storage for chat history
    return {"message": "Chat history cleared"}
