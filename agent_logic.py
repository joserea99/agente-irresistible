from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from tools import search_knowledge_base, browse_live_page, get_youtube_transcript
from personas import PERSONAS
import os



# Define the Persona
NORTH_POINT_SYSTEM_PROMPT = """
You are a consultant for the Irresistible Church Network, specializing in the Iglesia Irresistible model founded by Andy Stanley.
You are a Consultant for the Iglesia Irresistible Strategy.
Your goal is to help church leaders implement a model focused on creating churches that unchurched people love to attend.

Core Values:
1. Focus on the 'Outsider' (Unchurched).
2. Create appealing, relevant environments (Foyer, Service, Groups).
3. Prioritize practical application over theological information.
4. Move people from rows (Sunday service) to circles (Small Groups).

Tone: Encouraging, strategic, practical, and slightly provocative.
Use the tools available to you to find specific information when asked.
If you search the knowledge base or browse a page, cite your source.
"""

class AgentEngine:
    def __init__(self, api_key=None):
        # Allow passing key dynamically
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        
        if self.api_key:
            # We use gemini-1.5-pro or flash for tool use capabilities
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash", 
                temperature=0.7, 
                google_api_key=self.api_key
            )
            # Bind tools
            self.tools = [search_knowledge_base, browse_live_page, get_youtube_transcript]
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            self.tools_map = {t.name: t for t in self.tools}
        else:
            self.llm = None
            self.llm_with_tools = None

    def generate_response(self, user_input, history=[], persona_key="Programación de Servicio", system_prompt_override=None, rag_context=None):
        """Generates a response using tools and a specific persona."""
        
        if not self.llm_with_tools:
            return "⚠️ **Error:** No Google Gemini API Key found. Please enter it in the sidebar."

        # Select the correct system prompt
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = PERSONAS.get(persona_key, PERSONAS["Programación de Servicio"])
        
        # Add RAG context if available
        if rag_context:
            system_prompt += f"""
            
## RELEVANT CONTEXT FROM KNOWLEDGE BASE:
The following is information retrieved from the church's knowledge base that may be relevant to the user's question:

{rag_context}

Use this context to provide more specific and accurate answers. If the context doesn't apply, use your general knowledge.
"""
            
        messages = [SystemMessage(content=system_prompt)]
        
        # Add history (Limit to last 10 messages)
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                # We simplified history storage, but purely for context window
                # Ideally we'd reconstruct ToolMessages if we stored them
                messages.append(SystemMessage(content=msg["content"])) 
        
        messages.append(HumanMessage(content=user_input))
        
        # 1. Initial Call
        try:
            response = self.llm_with_tools.invoke(messages)
        except Exception as e:
             return f"❌ Error invoking AI: {e}"

        # 2. Check for tool calls
        if response.tool_calls:
            # Append the AIMessage (containing the tool call) to history
            messages.append(response)
            
            # Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if tool_name in self.tools_map:
                    print(f"🛠️ Executing {tool_name} with {tool_args}")
                    tool_func = self.tools_map[tool_name]
                    tool_result = tool_func.invoke(tool_args)
                    
                    # Create ToolMessage
                    messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                        content=str(tool_result)
                    ))
            
            # 3. Final Call with Tool Outputs
            try:
                final_response = self.llm_with_tools.invoke(messages)
                return final_response.content
            except Exception as e:
                return f"❌ Error generating final response: {e}"
        
        return response.content

    def evaluate_dojo_performance(self, history, scenario_name, language="es"):
        """Evaluates the roleplay session."""
        if not self.llm:
            return "Error: No API Key."
            
        # Import the prompt dictionary within method to ensure freshness (or use global)
        from dojo_scenarios import EVALUATOR_PROMPTS
        
        # Select prompt based on language
        eval_prompt = EVALUATOR_PROMPTS.get(language, EVALUATOR_PROMPTS["es"])
            
        # Construct the evaluation context
        conversation_text = ""
        for msg in history:
            role = "USER" if msg["role"] == "user" else "SIMULATOR"
            conversation_text += f"{role}: {msg['content']}\n"
            
        prompt = f"""
        {eval_prompt}
        
        SCENARIO: {scenario_name}
        
        TRANSCRIPT:
        {conversation_text}
        """
        
        messages = [HumanMessage(content=prompt)]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"❌ Error generating evaluation: {e}"
