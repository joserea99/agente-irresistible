from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from ..services.chat_service import ChatService
from ..services.chat_history_service import ChatHistoryService
from ..services.rag_service import RAGManager
from ..services.orchestrator_service import DirectorOrchestrator
from .auth import verify_active_user
import os
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

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

class CouncilRequest(BaseModel):
    """Request for multi-director council consultation."""
    question: str
    directors: Optional[List[str]] = None  # None = all directors
    session_id: Optional[str] = None
    rag_enabled: bool = False

class ConsultRequest(BaseModel):
    """Request for one director to consult another."""
    message: str
    session_id: Optional[str] = None
    primary_director: str = "Pastor Principal"
    consulting_directors: Optional[List[str]] = None  # None = auto-detect
    rag_enabled: bool = False
    auto_collaborate: bool = True

# Initialize chat service
def get_chat_service():
    api_key = os.environ.get("GOOGLE_API_KEY")
    return ChatService(api_key=api_key)

def get_history_service():
    return ChatHistoryService()

def get_orchestrator(chat_service: ChatService = Depends(get_chat_service)):
    return DirectorOrchestrator(chat_service=chat_service)

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
                logger.info(f"Created new chat session: {session_id}")
            else:
                logger.warning("Failed to create session. Chat will not be saved.")
        
        # 2. Save User Message
        history_service.add_message(session_id, "user", request.message)
        
        # 3. Load History for Context (Last 10 messages)
        # We fetch from DB to ensure context is accurate to what's stored
        db_messages = history_service.get_session_messages(session_id)
        history_dicts = [{"role": m["role"], "content": m["content"]} for m in db_messages]
        
        # 4. Generate Response
        # Get RAG context if enabled
        rag_context = None
        if request.rag_enabled:
            try:
                rag_manager = RAGManager()
                rag_context = rag_manager.search(request.message, n_results=3)
                if rag_context:
                    logger.info(f"RAG context injected ({len(rag_context)} chars) for session {session_id}")
            except Exception as rag_err:
                logger.warning(f"RAG search failed, continuing without context: {rag_err}")
        
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

@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    history_service: ChatHistoryService = Depends(get_history_service),
    current_user: dict = Depends(verify_active_user),
):
    """
    Stream an AI response token-by-token (plain-text chunked response).
    Session id/title are returned in response headers; the assistant message
    is persisted once streaming completes.
    """
    from urllib.parse import quote

    user_id = current_user.get("id")
    session_id = request.session_id
    session_title = None

    # 1. Ensure session exists
    if not session_id:
        title = " ".join(request.message.split()[:5]) + "..."
        session_id = history_service.create_session(user_id, request.director, title)
        session_title = title

    # 2. Save user message
    history_service.add_message(session_id, "user", request.message)

    # 3. Load history (exclude the just-saved current message)
    db_messages = history_service.get_session_messages(session_id)
    history_dicts = [{"role": m["role"], "content": m["content"]} for m in db_messages][:-1]

    # 4. RAG context
    rag_context = None
    if request.rag_enabled:
        try:
            rag_context = RAGManager().search(request.message, n_results=3)
        except Exception as rag_err:
            logger.warning(f"RAG search failed, continuing without context: {rag_err}")

    def event_generator():
        collected = []
        try:
            for chunk in chat_service.generate_response_stream(
                user_input=request.message,
                history=history_dicts,
                director=request.director,
                rag_context=rag_context,
            ):
                collected.append(chunk)
                yield chunk
        finally:
            full_text = "".join(collected).strip()
            if full_text:
                try:
                    history_service.add_message(session_id, "assistant", full_text)
                except Exception as save_err:
                    logger.error(f"Failed to save streamed assistant message: {save_err}")

    headers = {
        "X-Session-Id": session_id or "",
        "X-Session-Title": quote(session_title or ""),
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/railway)
        "Access-Control-Expose-Headers": "X-Session-Id, X-Session-Title",
    }
    return StreamingResponse(
        event_generator(),
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


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


# ─── Multi-Agent Endpoints ───────────────────────────────────────────


@router.post("/consult")
async def consult_directors(
    request: ConsultRequest,
    orchestrator: DirectorOrchestrator = Depends(get_orchestrator),
    history_service: ChatHistoryService = Depends(get_history_service),
    current_user: dict = Depends(verify_active_user),
):
    """
    Send a message to a primary director with optional cross-director consultation.
    When auto_collaborate=True, the system auto-detects which directors should contribute.
    """
    try:
        user_id = current_user.get("id")
        session_id = request.session_id
        session_title = None

        # Ensure session exists
        if not session_id:
            title = " ".join(request.message.split()[:5]) + "..."
            session_id = history_service.create_session(
                user_id, request.primary_director, title
            )
            session_title = title

        # Save user message
        history_service.add_message(session_id, "user", request.message)

        # Load history
        db_messages = history_service.get_session_messages(session_id)
        history_dicts = [{"role": m["role"], "content": m["content"]} for m in db_messages]

        # RAG context
        rag_context = None
        if request.rag_enabled:
            try:
                rag_manager = RAGManager()
                rag_context = rag_manager.search(request.message, n_results=3)
            except Exception as rag_err:
                logger.warning(f"RAG search failed: {rag_err}")

        # Multi-director response
        result = orchestrator.multi_director_response(
            question=request.message,
            primary_director=request.primary_director,
            history=history_dicts[:-1],
            rag_context=rag_context,
            auto_detect=request.auto_collaborate,
            consulting_directors=request.consulting_directors,
        )

        # Save AI response
        history_service.add_message(session_id, "assistant", result["message"])

        return {
            "message": result["message"],
            "session_id": session_id,
            "session_title": session_title,
            "primary_director": result["primary_director"],
            "consulted_directors": [
                {"director": c["director"], "status": c["status"]}
                for c in result["consulted_directors"]
            ],
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in consultation: {str(e)}")


@router.post("/council")
async def council_meeting(
    request: CouncilRequest,
    orchestrator: DirectorOrchestrator = Depends(get_orchestrator),
    current_user: dict = Depends(verify_active_user),
):
    """
    Council mode: get perspectives from multiple directors on the same question,
    plus an AI-generated synthesis with consensus points and next steps.
    """
    try:
        # RAG context
        rag_context = None
        if request.rag_enabled:
            try:
                rag_manager = RAGManager()
                rag_context = rag_manager.search(request.question, n_results=3)
            except Exception as rag_err:
                logger.warning(f"RAG search failed: {rag_err}")

        result = orchestrator.consensus_response(
            question=request.question,
            directors=request.directors,
            rag_context=rag_context,
        )

        return {
            "question": result["question"],
            "perspectives": result["perspectives"],
            "synthesis": result["synthesis"],
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in council: {str(e)}")
