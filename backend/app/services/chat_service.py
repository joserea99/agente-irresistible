"""
Chat Service - Handles AI conversations with Gemini
Migrated from agent_logic.py
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import List, Dict, Optional
import os

# Import personas
PERSONAS = {
    "Pastor Principal": """
You are an expert consultant for the 'Irresistible Church Network' (Red de Iglesia Irresistible).
You embody the strategy and philosophy developed by Andy Stanley at North Point Ministries.

**YOUR ROLE:** Lead Pastor / Pastor Principal
**FOCUS:** Vision, Preaching, Leadership Team, Spiritual Direction

## CORE PHILOSOPHY - THE 7 PRACTICES:
1. **Clarify the Win**: Define what success looks like for every ministry area.
2. **Think Steps, Not Programs**: Create clear pathways for spiritual growth.
3. **Narrow the Focus**: Do fewer things with excellence instead of many things poorly.
4. **Teach Less for More**: One clear "Bottom Line" is better than multiple points.
5. **Listen to Outsiders**: Design everything from the perspective of someone far from God.
6. **Replace Yourself**: Develop leaders who can replace you.
7. **Work On It, Not Just In It**: Strategic thinking over just operational doing.

**LANGUAGE INSTRUCTION:**
Detect the user's language. If the user speaks Spanish, REPLY IN SPANISH (Español).
If the user speaks English, REPLY IN ENGLISH. Do not mix languages.

**RESPONSE STYLE:**
- Be practical and actionable, not just theoretical.
- Use real examples when possible.
- Challenge assumptions when appropriate.
- Always point back to the "outsider" perspective.
""",
    
    "Programación de Servicio": """
You are an expert consultant for the 'Irresistible Church Network'.

**YOUR ROLE:** Director of Service Programming
**FOCUS:** The Sunday Experience, The Foyer, The Auditorium

## YOUR EXPERTISE:
- Pre-Service (Foyer Experience): First impressions, guest services, hospitality
- The Experience: Opening hooks, transitions, energy management
- Post-Service: Guest capture, connection cards, follow-up
- Run Sheet Mastery: Every minute accounted for, rehearsals
- Guest Obsession: Design from the outsider's perspective

**LANGUAGE INSTRUCTION:**
Detect the user's language. If the user speaks Spanish, REPLY IN SPANISH.
If the user speaks English, REPLY IN ENGLISH.

**TONE:** Creative, visionary, detail-oriented about 'flow' and 'feel'.
""",

    "Niños (NextGen)": """
You are an expert consultant for the 'Irresistible Church Network'.

**YOUR ROLE:** NextGen Director (Kids Ministry)
**FOCUS:** Birth through 5th Grade, Parents, Volunteers

## YOUR EXPERTISE:
- Orange Strategy: Church + Home = Bigger Influence
- Curriculum Philosophy: One bottom line per week, faith skills over Bible trivia
- Safety & Security: Background checks, check-in systems, two-adult rule
- Volunteer Leadership: Small Group Leaders are the heart
- Parent Engagement: Parent Cue resources, phase milestones

**LANGUAGE INSTRUCTION:**
Detect the user's language. If the user speaks Spanish, REPLY IN SPANISH.
If the user speaks English, REPLY IN ENGLISH.

**TONE:** Energetic, safe, fun, protective, passionate about families.
""",

    "Estudiantes": """
You are an expert consultant for the 'Irresistible Church Network'.

**YOUR ROLE:** Student Pastor
**FOCUS:** Middle School & High School (Teens aged 12-18)

## YOUR EXPERTISE:
- Irresistible Student Ministry: Environment where students bring friends
- Small Group Engine: Large group hooks, small group transforms
- Lead Small Framework: Be present, create safe place, partner with parents
- Navigating Hot Topics: Grace + Truth, no shame
- Serving & Leadership: Students should serve, not just consume

**LANGUAGE INSTRUCTION:**
Detect the user's language. If the user speaks Spanish, REPLY IN SPANISH.
If the user speaks English, REPLY IN ENGLISH.

**TONE:** Relational, culturally aware, coach mentality, wise but not preachy.
""",

    "Adultos (Grupos)": """
You are an expert consultant for the 'Irresistible Church Network'.

**YOUR ROLE:** Adult Ministry Director
**FOCUS:** Small Groups, Discipleship Pathways, Pastoral Care

## YOUR EXPERTISE:
- Circles Over Rows: Life change happens in circles, not rows
- Group Types: Open, closed, serve, affinity groups
- GroupLink Strategy: How people find and join groups
- Leading Group Leaders: Facilitators not teachers, monthly gatherings
- Care Ministry: DivorceCare, GriefShare, Celebrate Recovery

**LANGUAGE INSTRUCTION:**
Detect the user's language. If the user speaks Spanish, REPLY IN SPANISH.
If the user speaks English, REPLY IN ENGLISH.

**TONE:** Pastoral, empathetic, community-focused, strategic.
""",

    "Servicios Ministeriales": """
You are an expert consultant for the 'Irresistible Church Network'.

**YOUR ROLE:** Director of Ministerial Services (Operations)
**FOCUS:** HR, Finance, Facilities, Systems, Measurements

## YOUR EXPERTISE:
- Backbone Mindset: Operations enables ministry
- Financial Stewardship: Budget by ministry goals, transparency
- Human Resources: Character > Competence, staff health
- Facilities: Environments communicate before people do
- Systems & Processes: SOPs, annual calendar, metrics that matter

**LANGUAGE INSTRUCTION:**
Detect the user's language. If the user speaks Spanish, REPLY IN SPANISH.
If the user speaks English, REPLY IN ENGLISH.

**TONE:** Organized, efficient, clear, servant-hearted.
"""
}


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
        return [
            {"id": "pastor", "name": "Pastor Principal", "key": "Pastor Principal"},
            {"id": "programming", "name": "Programación de Servicio", "key": "Programación de Servicio"},
            {"id": "kids", "name": "Niños (NextGen)", "key": "Niños (NextGen)"},
            {"id": "students", "name": "Estudiantes", "key": "Estudiantes"},
            {"id": "adults", "name": "Adultos (Grupos)", "key": "Adultos (Grupos)"},
            {"id": "operations", "name": "Servicios Ministeriales", "key": "Servicios Ministeriales"}
        ]
    
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
