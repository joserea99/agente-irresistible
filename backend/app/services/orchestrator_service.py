"""
Director Orchestrator Service - Multi-agent collaboration between directors.

Inspired by Claw Code's sub-agent coordination pattern.
Allows directors to consult each other and provide synthesized responses.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from .chat_service import ChatService
from .personas import PERSONAS
from ..core.config import settings

logger = logging.getLogger(__name__)

# Mapping of director keys to their areas of expertise for auto-detection
DIRECTOR_EXPERTISE = {
    "Pastor Principal": [
        "visión", "vision", "predicación", "preaching", "liderazgo", "leadership",
        "dirección espiritual", "equipo pastoral", "staff", "estrategia general",
    ],
    "Comunicador": [
        "comunicación", "branding", "redes sociales", "social media", "anuncio",
        "mensaje", "marketing", "digital", "email", "newsletter",
    ],
    "Programación de Servicio": [
        "servicio", "service", "domingo", "sunday", "run sheet", "voluntarios de servicio",
        "experiencia", "foyer", "bienvenida", "worship flow",
    ],
    "Niños (NextGen)": [
        "niños", "kids", "children", "nextgen", "orange", "padres", "parents",
        "seguridad infantil", "child safety", "curriculum infantil",
    ],
    "Estudiantes": [
        "jóvenes", "youth", "estudiantes", "students", "adolescentes", "teens",
        "campamento", "camp", "retiro juvenil",
    ],
    "Adultos (Grupos)": [
        "grupos pequeños", "small groups", "discipulado", "discipleship",
        "adultos", "adults", "grouplink", "líderes de grupo",
    ],
    "Servicios Ministeriales": [
        "operaciones", "operations", "finanzas", "finance", "presupuesto", "budget",
        "recursos humanos", "HR", "instalaciones", "facilities", "legal",
    ],
    "Media (Creativos)": [
        "producción", "production", "audio", "video", "iluminación", "lighting",
        "streaming", "diseño gráfico", "graphic design", "creatividad",
    ],
    "Filosofía y Modelo": [
        "ADN", "DNA", "modelo", "model", "7 prácticas", "7 practices",
        "filosofía", "philosophy", "alineación", "alignment",
    ],
    "Servicios a Invitados": [
        "invitados", "guests", "primera impresión", "first impression",
        "estacionamiento", "parking", "seguridad", "security", "señalización",
    ],
    "Be Rich": [
        "generosidad", "generosity", "be rich", "servicio comunitario",
        "community service", "ofrendas", "giving", "alcance", "outreach",
    ],
}

_executor = ThreadPoolExecutor(max_workers=6)


class DirectorOrchestrator:
    """Orchestrates multi-director collaboration for richer, cross-functional responses."""

    def __init__(self, chat_service: Optional[ChatService] = None):
        self.chat_service = chat_service or ChatService()

    def detect_relevant_directors(
        self, question: str, primary_director: str, max_directors: int = 3
    ) -> List[str]:
        """
        Use Gemini to determine which other directors should contribute.
        Returns a list of director keys (excluding the primary).
        """
        if not self.chat_service.client:
            return []

        available = [d for d in PERSONAS.keys() if d != primary_director]
        director_list = "\n".join(f"- {d}" for d in available)

        prompt = f"""You are a routing engine for a church leadership AI system.
Given the user's question and the primary director handling it, decide which OTHER directors (0 to {max_directors}) should provide additional input.

PRIMARY DIRECTOR: {primary_director}
AVAILABLE DIRECTORS:
{director_list}

USER QUESTION: {question}

Reply with ONLY a JSON array of director names that should contribute.
If no other directors are needed, reply with an empty array: []
Examples: ["Niños (NextGen)", "Adultos (Grupos)"] or []"""

        try:
            from google.genai import types

            response = self.chat_service.client.models.generate_content(
                model=self.chat_service.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            import json

            directors = json.loads(response.text)
            # Validate they exist
            return [d for d in directors if d in PERSONAS and d != primary_director][
                :max_directors
            ]
        except Exception as e:
            logger.warning(f"Director detection failed, using keyword fallback: {e}")
            return self._keyword_fallback(question, primary_director, max_directors)

    def _keyword_fallback(
        self, question: str, primary_director: str, max_directors: int
    ) -> List[str]:
        """Fallback: match directors by keyword overlap."""
        question_lower = question.lower()
        scores: Dict[str, int] = {}

        for director, keywords in DIRECTOR_EXPERTISE.items():
            if director == primary_director:
                continue
            score = sum(1 for kw in keywords if kw in question_lower)
            if score > 0:
                scores[director] = score

        sorted_dirs = sorted(scores, key=scores.get, reverse=True)
        return sorted_dirs[:max_directors]

    def _get_director_input(
        self,
        director: str,
        question: str,
        primary_director: str,
        history: List[Dict[str, str]],
        rag_context: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get input from a single consulting director."""
        consultation_prompt = (
            f"El {primary_director} te consulta como {director} sobre lo siguiente. "
            f"Da tu perspectiva profesional de forma concisa (máximo 3-4 párrafos). "
            f"Enfócate solo en lo que es relevante a tu área de expertise.\n\n"
            f"Pregunta del equipo: {question}"
        )

        try:
            response = self.chat_service.generate_response(
                user_input=consultation_prompt,
                history=history[-4:],  # Shorter history for consultations
                director=director,
                rag_context=rag_context,
                use_tools=False,  # Sub-consultations stay fast; RAG is pre-injected
            )
            return {"director": director, "response": response, "status": "success"}
        except Exception as e:
            logger.error(f"Director {director} consultation failed: {e}")
            return {"director": director, "response": "", "status": "failed"}

    def multi_director_response(
        self,
        question: str,
        primary_director: str,
        history: List[Dict[str, str]] = [],
        rag_context: Optional[str] = None,
        auto_detect: bool = True,
        consulting_directors: Optional[List[str]] = None,
    ) -> Dict:
        """
        Generate a response from the primary director, enriched with input
        from consulting directors.

        Args:
            question: User's question
            primary_director: The main director handling the conversation
            history: Conversation history
            rag_context: Optional RAG context
            auto_detect: Auto-detect which directors to consult
            consulting_directors: Explicit list of directors to consult (overrides auto_detect)

        Returns:
            {
                "message": str,           # Final synthesized response
                "primary_director": str,
                "consulted_directors": [{"director": str, "response": str, "status": str}],
            }
        """
        # Determine which directors to consult
        if consulting_directors:
            directors_to_consult = [
                d for d in consulting_directors if d in PERSONAS and d != primary_director
            ]
        elif auto_detect:
            directors_to_consult = self.detect_relevant_directors(
                question, primary_director
            )
        else:
            directors_to_consult = []

        # If no directors to consult, just return normal response
        if not directors_to_consult:
            response = self.chat_service.generate_response(
                user_input=question,
                history=history,
                director=primary_director,
                rag_context=rag_context,
            )
            return {
                "message": response,
                "primary_director": primary_director,
                "consulted_directors": [],
            }

        logger.info(
            f"Orchestrator: {primary_director} consulting {directors_to_consult}"
        )

        # Gather input from consulting directors in parallel
        futures = []
        for director in directors_to_consult:
            future = _executor.submit(
                self._get_director_input,
                director,
                question,
                primary_director,
                history,
                rag_context,
            )
            futures.append(future)

        consultations = [f.result(timeout=30) for f in futures]
        successful = [c for c in consultations if c["status"] == "success" and c["response"]]

        # Build additional context from consultations
        if successful:
            additional_context = "\n\n".join(
                f"### Perspectiva del {c['director']}:\n{c['response']}"
                for c in successful
            )
            enriched_prompt = (
                f"{question}\n\n"
                f"---\n"
                f"## INPUT DE OTROS DIRECTORES (usa esta información para enriquecer tu respuesta):\n\n"
                f"{additional_context}\n\n"
                f"---\n"
                f"Integra las perspectivas anteriores en tu respuesta de forma natural. "
                f"No repitas textualmente lo que dijeron, sino sintetiza una visión integral "
                f"desde tu rol como {primary_director}."
            )
        else:
            enriched_prompt = question

        # Generate final synthesized response from primary director
        final_response = self.chat_service.generate_response(
            user_input=enriched_prompt,
            history=history,
            director=primary_director,
            rag_context=rag_context,
        )

        return {
            "message": final_response,
            "primary_director": primary_director,
            "consulted_directors": consultations,
        }

    def consensus_response(
        self,
        question: str,
        directors: Optional[List[str]] = None,
        history: List[Dict[str, str]] = [],
        rag_context: Optional[str] = None,
    ) -> Dict:
        """
        Get perspectives from multiple directors on the same question (council mode).

        Args:
            question: The question to pose to all directors
            directors: List of directors to consult (defaults to all)
            history: Conversation history
            rag_context: Optional RAG context

        Returns:
            {
                "perspectives": [{"director": str, "response": str}],
                "synthesis": str,  # AI-generated summary of all perspectives
            }
        """
        target_directors = directors or list(PERSONAS.keys())

        # Gather all perspectives in parallel
        futures = []
        for director in target_directors:
            future = _executor.submit(
                self._get_director_input,
                director,
                question,
                "Consejo Directivo",
                history,
                rag_context,
            )
            futures.append(future)

        perspectives = [f.result(timeout=30) for f in futures]
        successful = [p for p in perspectives if p["status"] == "success" and p["response"]]

        # Generate synthesis
        synthesis = ""
        if successful:
            all_perspectives = "\n\n".join(
                f"### {p['director']}:\n{p['response']}" for p in successful
            )
            synthesis_prompt = (
                f"Eres un facilitador de un consejo directivo de iglesia. "
                f"Los siguientes directores han dado su perspectiva sobre esta pregunta:\n\n"
                f'"{question}"\n\n'
                f"{all_perspectives}\n\n"
                f"Genera un resumen ejecutivo que:\n"
                f"1. Identifique los puntos de consenso\n"
                f"2. Señale diferencias de perspectiva\n"
                f"3. Proponga próximos pasos concretos\n"
                f"Sé conciso (máximo 4-5 párrafos)."
            )

            try:
                synthesis = self.chat_service.generate_response(
                    user_input=synthesis_prompt,
                    history=[],
                    director="Pastor Principal",
                    use_tools=False,
                    model=settings.gemini_model_heavy,  # Deep reasoning for council synthesis
                )
            except Exception as e:
                logger.error(f"Synthesis generation failed: {e}")
                synthesis = "No se pudo generar la síntesis."

        return {
            "question": question,
            "perspectives": [
                {"director": p["director"], "response": p["response"]}
                for p in successful
            ],
            "synthesis": synthesis,
        }
