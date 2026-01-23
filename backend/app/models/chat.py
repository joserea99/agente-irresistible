from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    persona: str = "Programación de Servicio"
    rag_enabled: bool = True

class ChatResponse(BaseModel):
    message: str
