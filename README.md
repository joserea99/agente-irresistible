# 🏙️ Sistema Operativo: Iglesia Irresistible (Agent App)

Una plataforma integral de Inteligencia Artificial diseñada para equipos ministeriales, experta en la estrategia de la **Iglesia Irresistible**.

## 🚀 Funcionalidades Principales

### 1. 🏛️ El Gabinete (Modo Consultor)
Obtén asesoría estratégica de 6 directores especializados. Selecciona con quién quieres hablar en la barra lateral:
- **Programación de Servicio:** Diseño de experiencias de domingo.
- **Niños (NextGen):** Estrategia Orange y seguridad.
- **Estudiantes:** Cultura juvenil y grupos pequeños.
- **Adultos:** Discipulado y cuidado pastoral.
- **Servicios Ministeriales:** Operaciones y sistemas.
- **Media:** Comunicación y creatividad.

### 2. 🥋 El Dojo (Simulador de Liderazgo)
Entrena tus habilidades de conversación en situaciones difíciles.
- **Modo Bilingüe:** Selecciona "Español" o "English".
- **Escenarios Reales:** "El Padre Enojado", "El Voluntario Agotado", "El Invitado Escéptico".
- **Evaluación en Tiempo Real:** Al terminar, recibe una calificación basada en los principios de la Iglesia Irresistible.

### 3. 🧠 Inteligencia Multimedia (Smart Crawl)
El agente puede aprender no solo leyendo, sino viendo y escuchando.
- Botón **"🕷️ Smart Crawl (Deep)"**: Navega el sitio `my.irresistible.church`.
- **Transcripción Automática:** Si encuentra videos o audios, los descarga, los transcribe (usando Gemini AI) y los guarda en su memoria.

### 4. 📄 Generador de Documentos
- Convierte cualquier conversación o plan en un documento de Word (`.docx`) listo para descargar y compartir con tu equipo.

---

## 🛠️ Instalación y Uso

### 1. Preparar el Entorno
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
```

### 2. Iniciar la App
```bash
./venv/bin/streamlit run app.py
```
Accede en tu navegador: `http://localhost:8501`

### 3. Configuración
- **API Key:** Requiere una Google Gemini API Key (gratuita en AI Studio).
- **Base de Datos:** Los usuarios y chats se guardan localmente en SQLite (`users.db`).
- **Memoria:** El conocimiento se guarda en `chroma_db/`.

---

## 📁 Estructura del Proyecto
- `app.py`: Interfaz de usuario (Streamlit).
- `agent_logic.py`: Cerebro del agente y manejo de prompts.
- `personas.py`: Definición de los 6 directores y sus personalidades.
- `dojo_scenarios.py`: Escenarios de roleplay (Español/Inglés).
- `media_processor.py`: Módulo de descarga y transcripción de video/audio.
- `browser_service.py`: Navegador autónomo para crawlers.
- `rag_manager.py`: Sistema de memoria vectorial.

---

## 🔑 Credenciales por Defecto
(Para pruebas locales)
- **Email:** `tester3@example.com`
- **Pass:** `pass`

¡Disfruta construyendo una iglesia irresistible!
