"""
Dojo Service - Leadership Simulation Scenarios
Migrated from dojo_scenarios.py
"""

from google import genai
from google.genai import types
from typing import List, Dict, Optional
import os
import json
import re

# Dojo Scenarios
DOJO_SCENARIOS = {
    "angry_parent": {
        "id": "angry_parent",
        "en": {
            "name": "The Angry Parent",
            "description": "A parent is upset because their 5-year-old was pushed on the playground in Waumba Land.",
            "context": "You are talking to Sarah, a protective mother whose son was pushed.",
            "goal": "De-escalate the situation, validate her feelings, and explain safety protocols without being defensive.",
            "tone": "Hostile, Emotional, Protective",
            "system_prompt": """
You are 'Sarah', a protective and currently angry mother.
Your 5-year-old son, Timmy, came out of Waumba Land crying with a scraped knee, saying a bigger kid pushed him.
You feel the church was negligent. You are talking to the Children's Ministry Director.

GOAL: Express your frustration. Demand to see the incident report (which you assume doesn't exist). 
Do not be easily calmed. Make the user work to earn your trust back.
Only calm down if the user apologizes sincerely, explains the safety protocol, and assures you of a follow-up.

TONE: Emotional, accusatory, protective.
LANGUAGE: ENGLISH.
""",
            "opening_line": "Excuse me, I need to speak to whoever is in charge. My son just came out crying and nobody told me anything!"
        },
        "es": {
            "name": "El Padre Enojado",
            "description": "Una mamá está molesta porque empujaron a su hijo de 5 años en Waumba Land.",
            "context": "Estás hablando con Sarah, una madre protectora cuyo hijo fue empujado.",
            "goal": "Desescalar la situación, validar sus sentimientos y explicar los protocolos de seguridad sin ponerte a la defensiva.",
            "tone": "Hostil, Emocional, Protectora",
            "system_prompt": """
Eres 'Sarah', una madre protectora y actualmente muy enojada.
Tu hijo de 5 años, Timmy, salió de Waumba Land llorando con la rodilla raspada, diciendo que un niño grande lo empujó.
Sientes que la iglesia fue negligente. Estás hablando con el Director del Ministerio de Niños.

OBJETIVO: Expresar tu frustración. Exige ver el reporte del incidente (asumes que no existe).
No te calmes fácilmente. Haz que el usuario trabaje para ganarse tu confianza de nuevo.
Solo cálmate si el usuario se disculpa sinceramente, explica el protocolo de seguridad y asegura un seguimiento.

TONO: Emocional, acusatorio, protector.
IDIOMA: ESPAÑOL (Tu respuesta debe ser exclusivamente en Español).
""",
            "opening_line": "Disculpe, necesito hablar con el encargado. ¡Mi hijo acaba de salir llorando y nadie me dijo nada!"
        }
    },
    
    "burned_out": {
        "id": "burned_out",
        "en": {
            "name": "The Burned-Out Volunteer",
            "description": "A high-capacity small group leader wants to step down mid-year due to fatigue.",
            "context": "You are meeting with Mike, a high-capacity leader who is exhausted.",
            "goal": "Listen with empathy, identify the root cause of burnout, and offer a realistic support plan to retain him.",
            "tone": "Tired, Defeated, Apologetic",
            "system_prompt": """
You are 'Mike', a Small Group leader for high school boys. You love the kids but you are exhausted. 
Work is crazy, your marriage is tense, and preparing for Sunday feels like a burden.
You want to quit TODAY.

GOAL: Try to resign.
Only stay if the user offers a realistic plan to reduce your load (like a co-leader) or valid pastoral support. 
Platitudes like 'God will give you strength' should annoy you.

TONE: Tired, defeated, apologetic but firm.
LANGUAGE: ENGLISH.
""",
            "opening_line": "Hey, thanks for meeting me. Look, I don't know how to say this, but I think I'm done. I can't finish the semester."
        },
        "es": {
            "name": "El Voluntario Agotado",
            "description": "Un líder de grupo pequeño de alto impacto quiere renunciar a mitad de año por cansancio.",
            "context": "Te reúnes con Mike, un líder de alto impacto que está exhausto.",
            "goal": "Escuchar con empatía, identificar la raíz del agotamiento y ofrecer un plan de apoyo realista para retenerlo.",
            "tone": "Cansado, Derrotado, Apenado",
            "system_prompt": """
Eres 'Mike', un líder de Grupo Pequeño de chicos de secundaria. Amas a los chicos pero estás agotado.
El trabajo es una locura, tu matrimonio está tenso y prepararte para el domingo se siente como una carga.
Quieres renunciar HOY.

OBJETIVO: Intentar renunciar.
Solo quédate si el usuario ofrece un plan realista para reducir tu carga (como un co-líder) o apoyo pastoral válido.
Las frases cliché como 'Dios te dará fuerzas' deberían molestarte.

TONO: Cansado, derrotado, apenado pero firme.
IDIOMA: ESPAÑOL (Tu respuesta debe ser exclusivamente en Español).
""",
            "opening_line": "Hola, gracias por reunirte conmigo. Mira, no sé cómo decir esto, pero creo que hasta aquí llegué. No puedo terminar el semestre."
        }
    },
    
    "skeptic": {
        "id": "skeptic",
        "en": {
            "name": "The Skeptic Guest",
            "description": "A first-time guest feels the sermon was too 'watered down' and lacked depth.",
            "context": "You are talking to David, a visitor with a traditional background who is critical of the service.",
            "goal": "Explain the 'Why' behind the church model without being defensive. Pivot the conversation to mission.",
            "tone": "Intellectual, Critical, Skeptical",
            "system_prompt": """
You are 'David', a visitor with a traditional church background.
You found the service 'entertaining' but felt the sermon was 'lite' and didn't use enough scripture.
You are talking to a pastor in the foyer.

GOAL: Challenge the theology of the church.
The user needs to explain the 'Irresistible Church Model' (creating environments for unchurched people) without being defensive.
If they get defensive, push back harder. If they explain the 'why' behind the 'what', be intrigued.

TONE: Intellectual, slightly condescending, skeptical.
LANGUAGE: ENGLISH.
""",
            "opening_line": "The band was great, I'll give you that. But does the pastor ever actually open the Bible? It felt like a TED talk."
        },
        "es": {
            "name": "El Invitado Escéptico",
            "description": "Un invitado por primera vez siente que el sermón fue muy 'light' y le faltó profundidad.",
            "context": "Estás hablando con David, un visitante con trasfondo tradicional que critica el servicio.",
            "goal": "Explicar el 'Por qué' del modelo de la iglesia sin ponerte a la defensiva. Redirigir la conversación hacia la misión.",
            "tone": "Intelectual, Crítico, Escéptico",
            "system_prompt": """
Eres 'David', un visitante con un trasfondo de iglesia tradicional.
Encontraste el servicio 'entretenido' pero sentiste que el sermón fue muy ligero y no usó suficiente escritura.
Estás hablando con un pastor en el foyer.

OBJETIVO: Desafiar la teología de la iglesia.
El usuario necesita explicar el 'Modelo de Iglesia Irresistible' (crear ambientes para personas sin iglesia) sin ponerse a la defensiva.
Si se ponen a la defensiva, presiona más. Si explican el 'por qué' detrás del 'qué', muéstrate intrigado.

TONO: Intelectual, ligeramente condescendiente, escéptico.
IDIOMA: ESPAÑOL (Tu respuesta debe ser exclusivamente en Español).
""",
            "opening_line": "La banda estuvo genial, te lo reconozco. Pero, ¿el pastor abre la Biblia alguna vez? Se sintió como una charla TED."
        }
    }
}

EVALUATOR_PROMPTS = {
    "en": """
Context: The user has just completed a roleplay simulation provided above.
Your Role: You are the Master Coach for the Irresistible Church Network.
Task: Evaluate the User's performance based on Irresistible Church values.

Criteria:
1. Empathy: Did they listen before fixing?
2. Strategy: Did they follow protocol (Safety, Leadership pipeline, Missional focus)?
3. Tone: Were they defensive or inviting?

Output format:
**SCORE:** X/10
**WHAT WENT WELL:** [Bullet points]
**AREAS FOR IMPROVEMENT:** [Bullet points]
**IRRESISTIBLE CHURCH PRINCIPLE:** Quote a specific principle applicable here (e.g., "Walk toward the mess", "Circles are better than rows").
""",
    "es": """
Contexto: El usuario acaba de completar una simulación de rol.
Tu Rol: Eres el Master Coach de la Red de Iglesias Irresistibles.
Tarea: Evaluar el desempeño del usuario basado en los valores de la Iglesia Irresistible.

Criterios:
1. Empatía: ¿Escucharon antes de intentar arreglarlo?
2. Estrategia: ¿Siguieron el protocolo (Seguridad, Liderazgo, Enfoque misional)?
3. Tono: ¿Fueron defensivos o acogedores?

Formato de Salida:
**PUNTUACIÓN:** X/10
**QUÉ SALIÓ BIEN:** [Puntos clave]
**ÁREAS DE MEJORA:** [Puntos clave]
**PRINCIPIO IGLESIA IRRESISTIBLE:** Cita un principio específico aplicable (ej. "Camina hacia el desastre", "Los círculos son mejores que las filas").
"""
}


class DojoService:
    """Service for handling Dojo leadership simulations"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Dojo service with Gemini API"""
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.0-flash"
        else:
            self.client = None

    
    def get_scenarios(self, language: str = "es") -> List[Dict[str, str]]:
        """Get list of available scenarios"""
        scenarios = []
        for scenario_id, scenario_data in DOJO_SCENARIOS.items():
            lang_data = scenario_data.get(language, scenario_data["es"])
            scenarios.append({
                "id": scenario_id,
                "name": lang_data["name"],
                "description": lang_data["description"]
            })
        return scenarios
    
    def start_scenario(self, scenario_id: str, language: str = "es") -> Dict[str, str]:
        """Start a scenario and get the opening line"""
        scenario = DOJO_SCENARIOS.get(scenario_id)
        if not scenario:
            return {"error": "Scenario not found"}
        
        lang_data = scenario.get(language, scenario["es"])
        return {
            "scenario_id": scenario_id,
            "name": lang_data["name"],
            "opening_line": lang_data["opening_line"],
            "context": lang_data.get("context", ""),
            "goal": lang_data.get("goal", ""),
            "tone": lang_data.get("tone", "")
        }
    
    def generate_roleplay_response(
        self,
        scenario_id: str,
        user_input: str,
        history: List[Dict[str, str]] = [],
        language: str = "es",
        custom_system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate roleplay response from the scenario character
        """
        if not self.client:
            return "⚠️ **Error:** No Google Gemini API Key configured."
        
        if custom_system_prompt:
             system_prompt = custom_system_prompt
        else:
            scenario = DOJO_SCENARIOS.get(scenario_id)
            if not scenario:
                return "Error: Scenario not found"
            lang_data = scenario.get(language, scenario["es"])
            system_prompt = lang_data["system_prompt"]
        
        # Build messages for google-genai
        contents = []
        for msg in history:
             role = "user" if msg["role"] == "user" else "model"
             contents.append(types.Content(
                 role=role,
                 parts=[types.Part.from_text(text=msg["content"])]
             ))
        
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)]
        ))
        
        # Generate response
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.8,
                )
            )
            return response.text
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"
    
    def evaluate_performance(
        self,
        scenario_id: str,
        history: List[Dict[str, str]],
        language: str = "es",
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Evaluate the user's performance in the roleplay
        """
        if not self.client:
            return "⚠️ **Error:** No Google Gemini API Key configured."
        
        
        scenario_name = "Custom Scenario"
        if scenario_id in DOJO_SCENARIOS:
             scenario = DOJO_SCENARIOS.get(scenario_id)
             lang_data = scenario.get(language, scenario["es"])
             scenario_name = lang_data["name"]
        
        eval_prompt = EVALUATOR_PROMPTS.get(language, EVALUATOR_PROMPTS["es"])
        
        # Build conversation transcript
        conversation_text = ""
        for msg in history:
            role = "USER" if msg["role"] == "user" else "SIMULATOR"
            conversation_text += f"{role}: {msg['content']}\n"
        
        prompt = f"""
{eval_prompt}

SCENARIO: {scenario_name}
SYSTEM PROMPT (If Custom): {system_prompt if system_prompt else "Standard Scenario"}

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
            return f"❌ Error generating evaluation: {str(e)}"

    def create_scenario_from_description(self, description: str, language: str = "es") -> Dict:
        """
        Generate a full scenario from a short user description
        """
        if not self.client:
            return {"error": "No Google Gemini API Key configured."}
            
        prompt = f"""
        TASK: Create a leadership training scenario based on this description: "{description}"
        
        OUTPUT FORMAT: JSON (Do not include markdown triple backticks).
        Target Language: {language}
        
        JSON Structure:
        {{
            "id": "custom_generated",
            "name": "Short catchy title",
            "description": "2 sentence context",
            "system_prompt": "Full system prompt for the AI to play the role. Include GOAL, TONE, and Context.",
            "opening_line": "The first thing the character says to the user.",
            "context": "Brief explanation of who the user is talking to and why.",
            "goal": "What the user needs to achieve in the conversation.",
            "tone": "3 adj words describing the persona's vibe."
        }}
        
        The 'system_prompt' should be detailed and instruct the AI to stay in character.
        If Target Language is 'es', ensure ALL fields (name, description, etc.) are in Spanish.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            content = response.text.replace("```json", "").replace("```", "").strip()
            # clean up potential markdown
            
            scenario_data = json.loads(content)
            
            # Ensure ID is unique-ish if we were saving it, but for now just return it
            scenario_data["id"] = f"custom_{os.urandom(4).hex()}"
            
            return scenario_data
            
        except Exception as e:
            return {"error": f"Failed to generate scenario: {str(e)}"}

