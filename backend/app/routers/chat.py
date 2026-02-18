from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from ..services.chat_service import ChatService
from ..services.chat_history_service import ChatHistoryService
from .auth import verify_active_user
import os
from io import BytesIO

router = APIRouter()

# Pydantic Models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    created_at: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    director: str = "Programación de Servicio"
    rag_enabled: bool = False
    history: List[Message] = [] # Optional, for context if sessions fail, but usually we load from DB

class ChatResponse(BaseModel):
    message: str
    session_id: Optional[str] = None
    session_title: Optional[str] = None

class ExportRequest(BaseModel):
    history: List[Message]
    title: str = "Conversación"

# Initialize chat service
def get_chat_service():
    api_key = os.environ.get("GOOGLE_API_KEY")
    return ChatService(api_key=api_key)

def get_history_service():
    return ChatHistoryService()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    history_service: ChatHistoryService = Depends(get_history_service),
    current_user: dict = Depends(verify_active_user)
):
    """
    Send a message and get AI response, saving history to DB.
    """
    try:
        user_id = current_user.get("id") # Username/Email from token
        session_id = request.session_id
        session_title = None
        
        # 1. Ensure Session Exists
        if not session_id:
            # Generate title from first message
            title = " ".join(request.message.split()[:5]) + "..."
            session_id = history_service.create_session(user_id, request.director, title)
            session_title = title
            if session_id:
                print(f"🆕 Created new chat session: {session_id}")
            else:
                print("⚠️ Failed to create session. Chat will not be saved.")
        
        # 2. Save User Message
        history_service.add_message(session_id, "user", request.message)
        
        # 3. Load History for Context (Last 10 messages)
        # We fetch from DB to ensure context is accurate to what's stored
        db_messages = history_service.get_session_messages(session_id)
        history_dicts = [{"role": m["role"], "content": m["content"]} for m in db_messages]
        
        # 4. Generate Response
        # Get RAG context if enabled (TODO: integrate RAG service)
        rag_context = None
        if request.rag_enabled:
            # TODO: Implement RAG search
            pass
        
        response_text = chat_service.generate_response(
            user_input=request.message,
            history=history_dicts[:-1], # Exclude current message as it's passed separately or double counted
            director=request.director,
            rag_context=rag_context
        )
        
        # 5. Save AI Response
        history_service.add_message(session_id, "assistant", response_text)
        
        return {
            "message": response_text, 
            "session_id": session_id,
            "session_title": session_title
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.get("/directors")
async def get_directors(chat_service: ChatService = Depends(get_chat_service)):
    return {"directors": chat_service.get_directors()}

@router.post("/export")
async def export_conversation(
    request: ExportRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    try:
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        docx_bytes = chat_service.export_conversation_to_docx(
            history=history_dicts,
            title=request.title
        )
        return StreamingResponse(
            BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={request.title}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting conversation: {str(e)}")

@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    history_service: ChatHistoryService = Depends(get_history_service),
    current_user: dict = Depends(verify_active_user)
):
    """Get list of past chat sessions"""
    try:
        # Use token user_id if 'current' requested
        target_user = current_user.get("id") if user_id == "current" else user_id
        
        # Security check: Users can only see their own history (unless admin - TODO)
        if target_user != current_user.get("id") and current_user.get("role") != "admin":
             raise HTTPException(status_code=403, detail="Access denied")

        sessions = history_service.get_user_sessions(target_user)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session_details(
    session_id: str,
    history_service: ChatHistoryService = Depends(get_history_service),
    current_user: dict = Depends(verify_active_user)
):
    """Get full message history for a session"""
    try:
        messages = history_service.get_session_messages(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    history_service: ChatHistoryService = Depends(get_history_service)
):
    """Delete a chat session"""
    try:
        history_service.delete_session(session_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
