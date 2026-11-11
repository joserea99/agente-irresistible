from google import genai
from google.genai import types
import os
import logging
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor

from ..core.config import settings
from .chat_service import ChatService

logger = logging.getLogger(__name__)

_pack_executor = ThreadPoolExecutor(max_workers=5)


class MagicService:
    """
    Service to transform content or sermon topics into complete ministerial deliverables
    ("Magic Actions" & "Sunday Production Pack").
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.google_api_key
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model = settings.gemini_model
        else:
            self.client = None

    def _call_llm(self, prompt: str) -> str:
        if not self.client:
            logger.error("GOOGLE_API_KEY not found in environment variables.")
            return "⚠️ Error: Configuración de API de Gemini no encontrada."
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.gemini_temperature,
                ),
            )
            return response.text or ""
        except Exception as e:
            logger.warning(f"Primary Gemini call failed on {self.model} ({e}); retrying with fallback...")
            try:
                fallback_model = "gemini-2.5-flash" if self.model != "gemini-2.5-flash" else "gemini-2.0-flash"
                response = self.client.models.generate_content(
                    model=fallback_model,
                    contents=prompt,
                )
                return response.text or ""
            except Exception as e2:
                logger.error(f"Gemini Generation Error: {e2}")
                return ChatService._format_friendly_error(e2)

    def generate_sermon_outline(self, content: str, language: str = "es") -> str:
        lang_name = "Español" if language == "es" else "English"
        prompt = f"""
        Actúa como el Pastor Principal y estratega de comunicación siguiendo la metodología de Andy Stanley ("Communicating for a Change" / Iglesia Irresistible).
        Diseña un **Bosquejo de Predicación de Un Solo Punto** listo para predicar a partir del siguiente tema, pasaje o contenido.

        **Idioma de salida:** {lang_name}
        **Formato:** Markdown ejecutivo, claro y estructurado.

        **Estructura obligatoria (Mapa de Mensaje de 5 Movimientos):**
        1. **Título Atractivo del Mensaje** (orientado a personas no creyentes o escépticas, sin jerga religiosa)
        2. **La Frase Memorable (The Big Idea):** Una sola oración corta, rítmica e inolvidable que resuma toda la enseñanza.
        3. **YO (Me) — Introducción y Tensión Personal (5-7 min):** Cómo presentar tu propia experiencia o dilema cotidiano para conectar con la audiencia.
        4. **NOSOTROS (We) — Tensión Común (5 min):** Por qué todos en el auditorio (creyentes y no creyentes) enfrentan este mismo problema y qué está en juego.
        5. **DIOS (God) — La Verdad Bíblica (12-15 min):** El pasaje bíblico central explicado en su contexto humano e histórico, desembocando en la Frase Memorable.
        6. **TÚ (You) — Aplicación Práctica (5-7 min):** Un reto específico, concreto y accionable para esta semana.
        7. **NOSOTROS (We) — Visión e Inspiración Final (3 min):** Qué pasaría en nuestras familias, ciudad e iglesia si todos viviéramos esta verdad, cerrando con oración.

        **Tema / Notas / Contenido base:**
        {content}

        IMPORTANTE: Todo el documento debe estar íntegramente en {lang_name}, con tono cálido, pastoral, contemporáneo y práctico.
        """
        return self._call_llm(prompt)

    def generate_small_group_guide(self, content: str, language: str = "es") -> str:
        lang_name = "Español" if language == "es" else "English"
        prompt = f"""
        Actúa como Director de Grupos Pequeños de North Point Ministries.
        Crea una **Guía de Discusión para Grupos Pequeños** lista para entregar a los líderes voluntarios.

        **Audiencia:** Adultos en grupos en casa
        **Formato:** Markdown limpio, listo para imprimir o enviar por WhatsApp
        **Idioma de salida:** {lang_name}
        
        **Estructura:**
        1. **Rompehielo (5 min):** 1 o 2 preguntas divertidas y fáciles de responder para que todos hablen desde el inicio.
        2. **La Idea Central:** Resumen en 2 líneas del enfoque del mensaje.
        3. **Preguntas de Conversación (30 min):** 4 preguntas abiertas (que NO se respondan con "sí" o "no" y que no requieran conocimiento bíblico previo) que lleven de la reflexión a la vulnerabilidad. Incluye una "Nota para el Líder" debajo de cada pregunta.
        4. **Paso Práctico de la Semana:** Un desafío concreto para aplicar antes del próximo domingo.
        5. **Guía de Oración Final:** Cómo cerrar el grupo orando unos por otros de forma sencilla.

        **Tema / Contenido base:**
        {content}
        
        IMPORTANTE: El resultado debe estar íntegramente en {lang_name}.
        """
        return self._call_llm(prompt)

    def generate_kids_lesson(self, content: str, language: str = "es") -> str:
        lang_name = "Español" if language == "es" else "English"
        prompt = f"""
        Actúa como Director de Niños y Familias (NextGen) utilizando la **Estrategia Orange** (Iglesia + Familia).
        Diseña una **Lección Dominical para Niños (Primaria / UpStreet)** alineada con el tema del domingo, pensada para ser ejecutada con materiales económicos y voluntarios.

        **Idioma de salida:** {lang_name}
        **Formato:** Markdown estructurado

        **Estructura:**
        1. **Verdad Básica y Frase Clave para Niños:** Una frase corta que un niño de 7 años pueda repetir de memoria.
        2. **Actividad de Bienvenida (10 min):** Juego rápido para romper el hielo usando materiales sencillos (vasos, papel, cinta, pelotas).
        3. **Historia Bíblica Creativa (12 min):** Cómo contar el pasaje bíblico de forma visual y participativa.
        4. **Aplicación en Grupo Pequeño (15 min):** Dinámica práctica y 3 preguntas adaptadas para niños.
        5. **Conexión con los Padres (Para el camino a casa):** Un mensaje corto listo para enviar a los papás por WhatsApp con 1 pregunta para hacerles a sus hijos durante el almuerzo del domingo.

        **Tema / Contenido base:**
        {content}

        IMPORTANTE: Todo el documento debe estar en {lang_name}. Nunca uses las palabras "ujieres" ni "acomodadores"; usa siempre "Anfitriones" o "Atención al Invitado".
        """
        return self._call_llm(prompt)

    def generate_service_runsheet(self, content: str, language: str = "es") -> str:
        lang_name = "Español" if language == "es" else "English"
        prompt = f"""
        Actúa como Director de Programación de Servicio (Service Programming Director) de una Iglesia Irresistible.
        Diseña el **Orden del Servicio Dominical (Run Sheet de 70 minutos)** y el guion del anfitrión (Host) para este domingo.

        **Idioma de salida:** {lang_name}
        **Formato:** Tabla Markdown + Guiones palabra por palabra

        **Estructura:**
        1. **Tabla de Minuto a Minuto (Run Sheet):** Columnas: Tiempo | Duración | Elemento | Responsable | Notas de Producción (Luces/Audio/Pantalla). Incluye desde Cuenta Regresiva (5 min), Canción de Apertura, Bienvenida del Host, Bloque de Alabanza, Transición/Video, Mensaje (35 min), Canción de Respuesta y Cierre.
        2. **Guion de Bienvenida del Host (60 segundos):** Qué decir exactamente para hacer sentir cómodos a quienes visitan por primera vez ("Nuestra iglesia fue pensada para ti").
        3. **Guion de Transición a la Ofrenda / Generosidad (60 segundos):** Conectado con la visión sin presionar a los invitados.
        4. **Guion de Despedida y Próximo Paso (60 segundos):** Invitación clara al siguiente domingo y a conectarse en el Foyer.

        **Tema / Contenido base:**
        {content}

        IMPORTANTE: Todo el documento debe estar en {lang_name}. Nunca uses las palabras "ujieres" ni "acomodadores"; usa siempre "Anfitriones" o "Atención al Invitado".
        """
        return self._call_llm(prompt)

    def generate_implementation_plan(self, content: str, language: str = "es") -> str:
        lang_name = "Español" if language == "es" else "English"
        prompt = f"""
        Actúa como Pastor Ejecutivo y Director de Operaciones Ministeriales.
        Crea un **Plan de Implementación de 4 Semanas** basado en las ideas estratégicas de este contenido.

        **Formato:** Tabla Markdown y Lista de Verificación (Checklist)
        **Idioma de salida:** {lang_name}
        
        **Estructura:**
        *   **Objetivo Estratégico:** Definición clara del "Win" (la victoria).
        *   **Semana 1: Alineación con Líderes y Preparación**
        *   **Semana 2: Comunicación y Reclutamiento de Voluntarios**
        *   **Semana 3: Lanzamiento y Ejecución**
        *   **Semana 4: Evaluación y Optimización**
        
        Para cada semana, incluye tareas específicas, responsables sugeridos y métricas de éxito.

        **Contexto/Contenido:**
        {content}
        
        IMPORTANTE: El resultado debe estar íntegramente en {lang_name}.
        """
        return self._call_llm(prompt)

    def generate_social_media_posts(self, content: str, language: str = "es") -> str:
        lang_name = "Español" if language == "es" else "English"
        prompt = f"""
        Actúa como Director de Comunicación Digital de una iglesia relevante.
        Crea un **Pack de Difusión Digital y WhatsApp** a partir de este tema o mensaje, diseñado para atraer a personas no creyentes y movilizar a la congregación.

        **Formato:** Markdown
        **Idioma de salida:** {lang_name}
        
        **Incluye:**
        1. **Guion para Reel / TikTok de Invitación (30 segundos):** Gancho en los primeros 3 segundos, desarrollo breve y llamado a la acción para este domingo.
        2. **Carrusel de Instagram (5 diapositivas):** Texto exacto de cada lámina + descripción (caption) para el post.
        3. **Post de Frase Memorable (Lunes post-domingo):** Para reforzar la idea central de la semana.
        4. **Mensaje de WhatsApp para toda la Iglesia (Viernes):** Texto cálido, corto y listo para copiar y pegar en el grupo de difusión de la iglesia para que inviten a un amigo el domingo.

        **Contexto/Contenido:**
        {content}
        
        IMPORTANTE: El resultado debe estar íntegramente en {lang_name}.
        """
        return self._call_llm(prompt)

    def generate_sunday_pack(
        self,
        topic: str,
        series_name: Optional[str] = None,
        scripture: Optional[str] = None,
        language: str = "es",
    ) -> Dict[str, str]:
        """
        Generate the complete 5-piece Sunday Production Pack in parallel.
        """
        context_parts = [f"Tema / Enfoque del Domingo: {topic}"]
        if series_name:
            context_parts.append(f"Serie de Predicación: {series_name}")
        if scripture:
            context_parts.append(f"Pasaje Bíblico de referencia: {scripture}")
        full_context = "\n".join(context_parts)

        tasks = {
            "sermon": _pack_executor.submit(self.generate_sermon_outline, full_context, language),
            "guide": _pack_executor.submit(self.generate_small_group_guide, full_context, language),
            "kids": _pack_executor.submit(self.generate_kids_lesson, full_context, language),
            "runsheet": _pack_executor.submit(self.generate_service_runsheet, full_context, language),
            "social": _pack_executor.submit(self.generate_social_media_posts, full_context, language),
        }

        results: Dict[str, str] = {}
        for key, future in tasks.items():
            try:
                results[key] = future.result(timeout=45)
            except Exception as e:
                logger.error(f"Error generating {key} in Sunday Pack: {e}")
                results[key] = f"Error al generar esta sección: {str(e)}"

        return results
