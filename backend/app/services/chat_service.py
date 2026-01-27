"""
Chat Service - Handles AI conversations with Gemini
Migrated from agent_logic.py
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import List, Dict, Optional
import os

# Import personas
from .personas import PERSONAS

class ChatService:
    """Service for handling AI chat conversations with Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat service with Gemini API"""
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.7,
                google_api_key=self.api_key
            )
        else:
            self.llm = None
    
    def get_directors(self) -> List[Dict[str, str]]:
        """Get list of available directors"""
        directors = []
        for key in PERSONAS.keys():
            # Create a simple ID from the name (e.g., "Pastor Principal" -> "pastor_principal")
            simple_id = key.lower().replace(" ", "_").replace("(", "").replace(")", "")
            directors.append({
                "id": simple_id,
                "name": key,
                "key": key
            })
        return directors
    
    def generate_response(
        self,
        user_input: str,
        history: List[Dict[str, str]] = [],
        director: str = "Programación de Servicio",
        rag_context: Optional[str] = None
    ) -> str:
        """
        Generate AI response
        
        Args:
            user_input: User's message
            history: Conversation history [{"role": "user"|"assistant", "content": "..."}]
            director: Director persona key
            rag_context: Optional context from knowledge base
            
        Returns:
            AI response string
        """
        if not self.llm:
            return "⚠️ **Error:** No Google Gemini API Key configured."
        
        # Get system prompt for selected director
        system_prompt = PERSONAS.get(director, PERSONAS["Programación de Servicio"])
        
        # Add RAG context if available
        if rag_context:
            system_prompt += f"""
            
## RELEVANT CONTEXT FROM KNOWLEDGE BASE:
The following is information retrieved from the church's knowledge base that may be relevant to the user's question:

{rag_context}

Use this context to provide more specific and accurate answers. If the context doesn't apply, use your general knowledge.
"""
        
        # Build messages
        messages = [SystemMessage(content=system_prompt)]
        
        # Add history (limit to last 10 messages)
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(SystemMessage(content=msg["content"]))
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        # Generate response
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"
    
    def export_conversation_to_docx(self, history: List[Dict[str, str]], title: str = "Conversación") -> bytes:
        """
        Export conversation to Word document
        
        Args:
            history: Conversation history
            title: Document title
            
        Returns:
            Bytes of the .docx file
        """
        from docx import Document
        from io import BytesIO
        
        doc = Document()
        doc.add_heading(title, 0)
        doc.add_paragraph(f"Exportado desde Iglesia Irresistible OS")
        doc.add_paragraph("")
        
        for msg in history:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            p = doc.add_paragraph()
            p.add_run(f"{role}: ").bold = True
            p.add_run(msg["content"])
            doc.add_paragraph("")
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def optimize_query(self, query: str) -> str:
        """
        Optimizes a search query by translating to English and expanding synonyms.
        """
        if not self.llm:
            return query
            
        prompt = f"""
        You are a search expert. The user is searching for assets in a DAM (Digital Asset Management) system.
        The assets are mostly in English.
        Convert the following search term (which may be in Spanish) into an optimized search query string.
        
        RULES:
        1. Translate to English if in Spanish.
        2. Keep the original term.
        3. Add 1-2 key synonyms.
        4. Join with 'OR'.
        5. Return ONLY the query string, nothing else.
        
        Input: "{query}"
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            cleaned = response.content.strip().replace('"', '')
            print(f"🔍 Optimized Query: '{query}' -> '{cleaned}'")
            return cleaned
        except Exception as e:
            print(f"❌ Error optimizing query: {e}")
            return query
