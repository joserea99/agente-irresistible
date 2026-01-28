from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from typing import Optional, List

class MagicService:
    """
    Service to transform content into specific deliverables ("Magic Actions").
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7,
                google_api_key=self.api_key
            )
        else:
            self.llm = None

    def _call_llm(self, prompt: str) -> str:
        if not self.llm:
            return "Error: Gemini API Key not configured."
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return f"Error generating content: {str(e)}"

    def generate_small_group_guide(self, content: str, language: str = "en") -> str:
        prompt = f"""
        You are an expert curriculum developer for North Point Ministries.
        Create a **Small Group Discussion Guide** based on the following content (e.g., a sermon transcript or article).

        **Target Audience:** Adults
        **Format:** Markdown
        **Output Language:** {language}
        
        **Structure:**
        1. **Icebreaker** (Fun, low stakes question related to the theme)
        2. **The Big Idea** (1 sentence summary of the content)
        3. **Discussion Questions** (3-5 open-ended questions that provoke thought, not just recall)
        4. **Application** (Practical "homework" or challenge for the week)
        5. **Prayer** (Simple closing)

        **Context/Content:**
        {content}
        
        IMPORTANT: The output must be entirely in {language}.
        """
        return self._call_llm(prompt)

    def generate_implementation_plan(self, content: str, language: str = "en") -> str:
        prompt = f"""
        You are an Executive Pastor and Project Manager.
        Create a **4-Week Implementation Plan** based on the strategic ideas in this content.

        **Format:** Markdown Table and Checklist
        **Output Language:** {language}
        
        **Structure:**
        *   **Objective:** Clear goal definition.
        *   **Week 1: Preparation & Consensus**
        *   **Week 2: Communication**
        *   **Week 3: Execution/Launch**
        *   **Week 4: Review & Optimaze**
        
        For each week, provide specific, actionable steps based on the text provided.

        **Context/Content:**
        {content}
        
        IMPORTANT: The output must be entirely in {language}.
        """
        return self._call_llm(prompt)

    def generate_social_media_posts(self, content: str, language: str = "en") -> str:
        prompt = f"""
        You are a Social Media Manager for a church.
        Extract **3 Core Insights** from this content and turn them into Instagram Captions.

        **Format:** Markdown
        **Output Language:** {language}
        
        **Output for each post:**
        *   **Hook:** Catchy first line.
        *   **Body:** The insight (short & punchy).
        *   **Call to Action:** Question or prompt for comments.
        *   **Hashtags:** Relevant tags (e.g., #IrresistibleChurch #Leadership).

        **Context/Content:**
        {content}
        
        IMPORTANT: The output must be entirely in {language}.
        """
        return self._call_llm(prompt)
