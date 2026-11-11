from google import genai
from google.genai import types
from .tools import search_knowledge_base, browse_live_page, get_youtube_transcript
from .personas import PERSONAS
from .dojo_scenarios import EVALUATOR_PROMPTS
import os
import inspect
import logging

logger = logging.getLogger(__name__)


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
    def __init__(self, api_key=None, mcp_registry=None, user_role="member"):
        # Allow passing key dynamically
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.mcp_registry = mcp_registry
        self.user_role = user_role

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.5-flash"

            # Map tools for execution (builtin + MCP)
            self.tools_map = {
                "search_knowledge_base": search_knowledge_base,
                "browse_live_page": browse_live_page,
                "get_youtube_transcript": get_youtube_transcript
            }

            # Register MCP tools in the tools map
            if self.mcp_registry:
                mcp_tools = self.mcp_registry.get_available_tools(user_role=self.user_role)
                for tool in mcp_tools:
                    self.tools_map[tool["name"]] = self._make_mcp_tool_caller(
                        tool["server"], tool["original_name"]
                    )
                if mcp_tools:
                    logger.info(f"AgentEngine: registered {len(mcp_tools)} MCP tool(s) for role {user_role}")

            self.tools_config = [search_knowledge_base, browse_live_page, get_youtube_transcript]

        else:
            self.client = None

    def _make_mcp_tool_caller(self, server_name: str, tool_name: str):
        """Create a callable wrapper for an MCP tool."""
        registry = self.mcp_registry
        role = self.user_role

        def mcp_tool_call(**kwargs):
            result = registry.call_tool(server_name, tool_name, kwargs, user_role=role)
            return str(result)

        mcp_tool_call.__name__ = f"mcp__{server_name}__{tool_name}"
        mcp_tool_call.__doc__ = f"MCP tool: {tool_name} from {server_name}"
        return mcp_tool_call

    def generate_response(self, user_input, history=[], persona_key="Programación de Servicio", system_prompt_override=None, rag_context=None):
        """Generates a response using tools and a specific persona."""
        
        if not self.client:
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
            
        contents = []
        # Add history
        for msg in history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            if "role" in msg and msg["role"] == "tool":
                 # Skip tool messages in history for now or handle them if structure matched
                 continue 
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))
        
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)]
        ))
        
        # 1. Initial Call with Tools
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    tools=self.tools_config # Pass python functions directly
                )
            )
        except Exception as e:
             return f"❌ Error invoking AI: {e}"

        # 2. Check for tool calls
        # google-genai response object has 'candidates' -> 'content' -> 'parts' -> 'function_call'
        # But SDK might have helper properties.
        # response.function_calls is a list if present.
        
        if response.function_calls:
            # We need to execute the function calls and send back the results
            
            # Start a chat session or append to contents to continue conversation
            # Constructing the tool response manually
            
            # Add the model's response (tool call) to history
            contents.append(response.candidates[0].content)
            
            for tool_call in response.function_calls:
                tool_name = tool_call.name
                tool_args = tool_call.args
                
                if tool_name in self.tools_map:
                    print(f"🛠️ Executing {tool_name} with {tool_args}")
                    tool_func = self.tools_map[tool_name]
                    
                    try:
                        # Invoke based on args dict
                        tool_result = tool_func.invoke(tool_args)
                    except:
                        # Fallback if invoke pattern matches or just call
                         tool_result = tool_func(**tool_args)
                    
                    # Create Tool Response Part
                    contents.append(types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name=tool_name,
                            response={"result": str(tool_result)} 
                        )]
                    ))
            
            # 3. Final Call with Tool Outputs
            try:
                final_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                     config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7
                    )
                )
                return final_response.text
            except Exception as e:
                return f"❌ Error generating final response: {e}"
        
        return response.text

    def evaluate_dojo_performance(self, history, scenario_name, language="es"):
        """Evaluates the roleplay session."""
        if not self.client:
            return "Error: No API Key."
            
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
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Error generating evaluation: {e}"
