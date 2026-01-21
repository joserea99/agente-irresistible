import streamlit as st
import time
import os
from database import verify_user, add_user, save_message, get_chat_history, init_db
from agent_logic import AgentEngine
from rag_manager import RAGManager
from browser_service import BrowserService
from media_processor import process_media_url
from personas import PERSONAS
from dojo_scenarios import DOJO_SCENARIOS
from utils import create_docx
from dotenv import load_dotenv

load_dotenv()

# ============== IRRESISTIBLE CHURCH CREDENTIALS ==============
IRRESISTIBLE_EMAIL = "jose.rea@lbne.org"
IRRESISTIBLE_PASSWORD = "jajciX-pohto7-dyd"
IRRESISTIBLE_URL = "https://my.irresistible.church/irresistiblechurchnetwork"

# ============== PREMIUM CSS ==============
CUSTOM_CSS = """
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .hero-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .hero-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Stat Cards */
    .stat-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.2);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Chat Container */
    .chat-container {
        background: rgba(26, 26, 46, 0.8);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Director Cards */
    .director-card {
        background: linear-gradient(145deg, #1e1e3f, #2a2a5a);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .director-card:hover {
        border-left-color: #764ba2;
        transform: translateX(5px);
    }
    
    /* Dojo Mode */
    .dojo-active {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        color: white;
        font-weight: 600;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar Enhancement */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a2e 100%);
    }
    
    /* Status Badge */
    .status-online {
        background: #22c55e;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Feature Cards */
    .feature-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
</style>
"""

# Initialize components
if "agent" not in st.session_state:
    st.session_state.agent = AgentEngine()
    
if "rag" not in st.session_state:
    st.session_state.rag = RAGManager()

def main():
    st.set_page_config(
        page_title="Iglesia Irresistible OS", 
        page_icon="⛪", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject Custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        login_page()
    else:
        dashboard()

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="hero-header">
            <h1>⛪ Iglesia Irresistible</h1>
            <p>Sistema Operativo Ministerial</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("📧 Email")
                password = st.text_input("🔑 Contraseña", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)
                
                if submitted:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.user = {"username": username, "name": user[0], "role": user[1]}
                        st.success(f"¡Bienvenido, {user[0]}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Credenciales inválidas")

        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("📧 Email")
                new_pass = st.text_input("🔑 Contraseña", type="password")
                new_name = st.text_input("👤 Nombre Completo")
                submitted = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
                if submitted:
                    if add_user(new_user, new_pass, new_name):
                        st.success("¡Cuenta creada! Inicia sesión.")
                    else:
                        st.error("El usuario ya existe.")

def dashboard():
    user = st.session_state.user
    
    # ============ SIDEBAR ============
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem;">👤</div>
            <h3 style="margin: 0.5rem 0;">{user['name']}</h3>
            <span class="status-online">● En línea</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Language
        language = st.selectbox("🌐 Idioma", ["Español", "English"])
        lang_code = "es" if language == "Español" else "en"
        
        st.divider()
        
        # Mode Selection with visual cards
        mode = st.radio(
            "🎯 Modo de Operación",
            ["🏛️ El Gabinete (Consultor)", "🥋 El Dojo (Roleplay)", "📊 Dashboard"],
            label_visibility="visible"
        )
        
        selected_persona = None
        selected_scenario = None
        
        if "Gabinete" in mode:
            st.markdown("### 🏛️ Directores Disponibles")
            selected_persona = st.selectbox(
                "Selecciona Director:",
                options=list(PERSONAS.keys()),
                index=0
            )
            st.info(f"💬 Conversando con: **{selected_persona}**")
            
        elif "Dojo" in mode:
            st.markdown("### 🥋 Escenarios de Entrenamiento")
            scenario_key = st.selectbox(
                "Elige Escenario:",
                options=list(DOJO_SCENARIOS.keys())
            )
            selected_scenario = scenario_key
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Iniciar", use_container_width=True):
                    st.session_state.messages = []
                    scenario_root = DOJO_SCENARIOS[scenario_key]
                    scenario_data = scenario_root.get(lang_code, scenario_root["es"])
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"**[{scenario_data['name']}]**\n\n{scenario_data['opening_line']}"
                    })
                    st.session_state.dojo_active = True
                    st.session_state.current_scenario_key = scenario_key
                    st.session_state.current_lang_code = lang_code
                    st.rerun()
            with col2:
                if st.button("🎯 Evaluar", use_container_width=True):
                    if st.session_state.get("dojo_active"):
                        eval_result = st.session_state.agent.evaluate_dojo_performance(
                            st.session_state.messages, 
                            st.session_state.current_scenario_key,
                            language=st.session_state.get("current_lang_code", "es")
                        )
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"**🥋 EVALUACIÓN:**\n\n{eval_result}"
                        })
                        st.session_state.dojo_active = False
                        st.rerun()
        
        st.divider()
        
        # Knowledge Base Section
        with st.expander("🧠 Base de Conocimiento", expanded=False):
            stats = st.session_state.rag.get_stats()
            st.metric("Documentos Indexados", stats)
            
            uploaded_file = st.file_uploader(
                "Subir archivo", 
                type=["pdf", "xlsx", "csv", "txt"],
                label_visibility="collapsed"
            )
            
            if uploaded_file and st.button("📥 Procesar", use_container_width=True):
                with st.spinner("Procesando..."):
                    try:
                        text = ""
                        file_type = uploaded_file.name.split(".")[-1].lower()
                        
                        if file_type == "pdf":
                            import pypdf
                            reader = pypdf.PdfReader(uploaded_file)
                            for page in reader.pages:
                                text += page.extract_text() + "\n"
                        elif file_type in ["xlsx", "csv"]:
                            import pandas as pd
                            if file_type == "xlsx":
                                df = pd.read_excel(uploaded_file)
                            else:
                                df = pd.read_csv(uploaded_file)
                            text = df.to_string(index=False)
                        elif file_type == "txt":
                            text = uploaded_file.read().decode("utf-8")
                        
                        if text:
                            st.session_state.rag.add_document(
                                content=text,
                                source_url=uploaded_file.name,
                                title=f"File: {uploaded_file.name}"
                            )
                            st.success("✅ Indexado!")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # ========== SMART CRAWL ==========
        st.divider()
        st.markdown("### 🕷️ Smart Crawl")
        st.caption("Navega, APRENDE y robustece tu base de conocimiento")
        
        # Topic input - now used for PRIORITIZATION, not filtering
        search_topic = st.text_input(
            "🎯 ¿Sobre qué tema quieres aprender?",
            placeholder="Ej: grupos pequeños, liderazgo, niños, worship...",
            key="crawl_topic",
            help="El sistema aprenderá TODO lo que encuentre, pero priorizará páginas relacionadas con tu tema."
        )
        
        crawl_depth = st.slider("Profundidad de navegación", 1, 5, 3, key="crawl_depth")
        max_pages = st.slider("Máximo de páginas a estudiar", 10, 150, 50, key="max_pages")
        
        # Learning mode toggle
        learn_all = st.checkbox("📚 Modo Aprendizaje Total", value=True, 
            help="Aprende de TODAS las páginas, no solo las que coinciden con el tema")
        
        if st.button("🧠 Iniciar Aprendizaje", use_container_width=True):
            if not search_topic:
                st.warning("⚠️ Por favor escribe un tema para enfocar el aprendizaje")
            else:
                # Statistics tracking
                stats = {
                    "urls_visited": [],
                    "pages_indexed": 0,
                    "pages_prioritized": 0,  # Related to topic
                    "errors": []
                }
                
                # Create UI containers
                progress_bar = st.progress(0)
                log_area = st.empty()
                indexed_list = []  # Track what we indexed
                
                # Normalize topic for flexible matching
                def normalize_text(text):
                    """Remove spaces, lowercase, for flexible matching"""
                    return ''.join(text.lower().split())
                
                def fuzzy_match(topic, content):
                    """Flexible matching that handles variations"""
                    topic_normalized = normalize_text(topic)
                    content_normalized = normalize_text(content)
                    
                    # Check normalized match
                    if topic_normalized in content_normalized:
                        return True
                    
                    # Check each word
                    topic_words = topic.lower().split()
                    content_lower = content.lower()
                    
                    matches = sum(1 for word in topic_words if word in content_lower)
                    return matches >= len(topic_words) * 0.5  # At least 50% of words match
                
                st.info(f"🎯 Aprendiendo sobre: **{search_topic}** | Modo: {'📚 Aprender Todo' if learn_all else '🔍 Solo Relevantes'}")
                
                try:
                    log_area.markdown("🔐 Conectando a irresistible.church...")
                    browser = BrowserService()
                    login_success = browser.login(IRRESISTIBLE_EMAIL, IRRESISTIBLE_PASSWORD)
                    
                    if login_success:
                        log_area.markdown("✅ Conectado! Iniciando aprendizaje...")
                        
                        # Crawl and LEARN
                        visited = set()
                        to_visit = [(IRRESISTIBLE_URL, 0)]
                        all_media = {"videos": [], "audios": [], "pdfs": []}
                        pages_data = []
                        
                        while to_visit and len(visited) < max_pages:
                            current_url, depth = to_visit.pop(0)
                            
                            if current_url in visited or depth > crawl_depth:
                                continue
                            
                            visited.add(current_url)
                            stats["urls_visited"].append(current_url)
                            progress_bar.progress(min(len(visited) / max_pages, 0.99))
                            log_area.markdown(f"🧠 **[{len(visited)}/{max_pages}]** Estudiando: `{current_url[:45]}...`")
                            
                            try:
                                # Ensure we're still logged in before each navigation
                                browser.ensure_logged_in()
                                browser.page.goto(current_url, timeout=15000)
                                
                                # Skip if we got redirected to login
                                if "sign" in browser.page.url.lower() or "login" in browser.page.url.lower():
                                    log_area.markdown(f"⚠️ Redirigido al login, intentando re-autenticar...")
                                    browser.ensure_logged_in()
                                    continue
                                
                                content_data = browser.get_page_content()
                                
                                if content_data and content_data.get('content'):
                                    title = content_data.get('title', 'Sin título')
                                    content = content_data['content']
                                    url = content_data['url']
                                    
                                    # Collect ALL media (regardless of topic match)
                                    if content_data.get('media_links'):
                                        for media_url in content_data['media_links']:
                                            ml = media_url.lower()
                                            if any(ext in ml for ext in ['.mp4', '.mov', '.webm', '.avi']):
                                                all_media["videos"].append(media_url)
                                            elif any(ext in ml for ext in ['.mp3', '.wav', '.m4a', '.ogg']):
                                                all_media["audios"].append(media_url)
                                            elif '.pdf' in ml:
                                                all_media["pdfs"].append(media_url)
                                    
                                    # Check relevance using fuzzy matching
                                    is_priority = fuzzy_match(search_topic, content) or fuzzy_match(search_topic, title) or fuzzy_match(search_topic, url)
                                    
                                    # LEARN mode: Index EVERYTHING or only relevant
                                    should_index = learn_all or is_priority
                                    
                                    if should_index and len(content) > 100:  # Avoid empty/tiny pages
                                        # INDEX TO KNOWLEDGE BASE
                                        st.session_state.rag.add_document(
                                            content=content,
                                            source_url=url,
                                            title=title
                                        )
                                        stats["pages_indexed"] += 1
                                        pages_data.append({"title": title, "url": url, "priority": is_priority})
                                        
                                        if is_priority:
                                            stats["pages_prioritized"] += 1
                                            log_area.markdown(f"⭐ **[PRIORITARIO]** Aprendido: {title[:40]}")
                                            indexed_list.append(f"⭐ {title[:50]}")
                                        else:
                                            log_area.markdown(f"📚 Aprendido: {title[:40]}")
                                            indexed_list.append(f"📚 {title[:50]}")
                                
                                # Get links for deeper exploration
                                if depth < crawl_depth:
                                    links = browser.page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
                                    for link in links:
                                        if "irresistible" in link and link not in visited and "logout" not in link.lower():
                                            if link.startswith("http"):
                                                to_visit.append((link, depth + 1))
                                                
                            except Exception as e:
                                stats["errors"].append(f"{current_url[:30]}: {str(e)[:50]}")
                                log_area.markdown(f"⚠️ Error: {str(e)[:40]}")
                        
                        browser.close()
                        progress_bar.progress(1.0)
                        
                        # ===== COMPREHENSIVE LEARNING REPORT =====
                        st.markdown("---")
                        st.markdown("## 🧠 Reporte de Aprendizaje")
                        
                        # Success message
                        st.success(f"✅ **¡Aprendizaje completado!** Se indexaron {stats['pages_indexed']} páginas a la base de conocimiento.")
                        
                        # Quick stats
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("🔍 URLs Exploradas", len(stats["urls_visited"]))
                        with col2:
                            st.metric("📚 Páginas Aprendidas", stats["pages_indexed"])
                        with col3:
                            st.metric("⭐ Prioritarias (tema)", stats["pages_prioritized"])
                        with col4:
                            total_media = len(all_media["videos"]) + len(all_media["audios"]) + len(all_media["pdfs"])
                            st.metric("🎬 Media Detectada", total_media)
                        
                        # Media breakdown
                        if all_media["videos"] or all_media["audios"] or all_media["pdfs"]:
                            st.markdown("### 📹 Archivos Multimedia Detectados")
                            
                            # Store media in session for later transcription
                            st.session_state["found_media"] = all_media
                            
                            if all_media["videos"]:
                                with st.expander(f"🎬 Videos ({len(all_media['videos'])})"):
                                    for v in all_media["videos"][:20]:
                                        st.markdown(f"- `{v.split('/')[-1]}`")
                            
                            if all_media["audios"]:
                                with st.expander(f"🎧 Audios ({len(all_media['audios'])})"):
                                    for a in all_media["audios"][:20]:
                                        st.markdown(f"- `{a.split('/')[-1]}`")
                            
                            if all_media["pdfs"]:
                                with st.expander(f"📄 PDFs ({len(all_media['pdfs'])})"):
                                    for p in all_media["pdfs"][:20]:
                                        st.markdown(f"- `{p.split('/')[-1]}`")
                            
                            # Transcription section
                            st.markdown("### 🎧 Transcripción de Multimedia")
                            st.caption("Descarga y transcribe videos/audios usando Gemini AI")
                            
                            transcribe_videos = all_media["videos"][:5]  # Limit to 5
                            transcribe_audios = all_media["audios"][:5]
                            
                            if transcribe_videos or transcribe_audios:
                                total_to_transcribe = len(transcribe_videos) + len(transcribe_audios)
                                st.info(f"📝 {total_to_transcribe} archivos listos para transcribir (máx 5 de cada tipo)")
                                
                                if st.button("🚀 Transcribir Multimedia", key="transcribe_media_btn"):
                                    transcribe_progress = st.progress(0)
                                    transcribe_log = st.empty()
                                    transcribed_count = 0
                                    total = len(transcribe_videos) + len(transcribe_audios)
                                    
                                    # Transcribe videos
                                    for idx, video_url in enumerate(transcribe_videos):
                                        transcribe_log.markdown(f"🎬 Descargando video: `{video_url.split('/')[-1]}`...")
                                        try:
                                            transcript = process_media_url(video_url)
                                            if transcript and "Error" not in transcript:
                                                st.session_state.rag.add_document(
                                                    content=f"TRANSCRIPCIÓN DE VIDEO: {video_url}\n\n{transcript}",
                                                    source_url=video_url,
                                                    title=f"Video: {video_url.split('/')[-1]}"
                                                )
                                                transcribed_count += 1
                                                transcribe_log.markdown(f"✅ Video transcrito: `{video_url.split('/')[-1]}`")
                                            else:
                                                transcribe_log.markdown(f"⚠️ Error en video: {transcript[:50] if transcript else 'Unknown error'}")
                                        except Exception as e:
                                            transcribe_log.markdown(f"❌ Error: {str(e)[:50]}")
                                        transcribe_progress.progress((idx + 1) / total)
                                    
                                    # Transcribe audios
                                    for idx, audio_url in enumerate(transcribe_audios):
                                        transcribe_log.markdown(f"🎧 Descargando audio: `{audio_url.split('/')[-1]}`...")
                                        try:
                                            transcript = process_media_url(audio_url)
                                            if transcript and "Error" not in transcript:
                                                st.session_state.rag.add_document(
                                                    content=f"TRANSCRIPCIÓN DE AUDIO: {audio_url}\n\n{transcript}",
                                                    source_url=audio_url,
                                                    title=f"Audio: {audio_url.split('/')[-1]}"
                                                )
                                                transcribed_count += 1
                                                transcribe_log.markdown(f"✅ Audio transcrito: `{audio_url.split('/')[-1]}`")
                                            else:
                                                transcribe_log.markdown(f"⚠️ Error en audio: {transcript[:50] if transcript else 'Unknown error'}")
                                        except Exception as e:
                                            transcribe_log.markdown(f"❌ Error: {str(e)[:50]}")
                                        transcribe_progress.progress((len(transcribe_videos) + idx + 1) / total)
                                    
                                    transcribe_progress.progress(1.0)
                                    st.success(f"🎉 ¡Transcripción completada! {transcribed_count}/{total} archivos procesados.")
                                    st.balloons()
                        else:
                            st.info("ℹ️ No se detectaron archivos multimedia (videos, audios, PDFs) en las páginas visitadas.")
                        
                        # Pages learned
                        if pages_data:
                            st.markdown("### 📚 Páginas Indexadas en Base de Conocimiento")
                            with st.expander(f"Ver {len(pages_data)} páginas aprendidas"):
                                for p in pages_data:
                                    icon = "⭐" if p.get('priority') else "📄"
                                    st.markdown(f"- {icon} [{p.get('title', 'Sin título')[:50]}]({p['url']})")
                        
                        # All URLs visited
                        with st.expander(f"🔍 Todas las URLs visitadas ({len(stats['urls_visited'])})"):
                            for url in stats["urls_visited"]:
                                st.markdown(f"- `{url[:70]}...`")
                        
                        # Errors if any
                        if stats["errors"]:
                            with st.expander(f"⚠️ Errores ({len(stats['errors'])})"):
                                for err in stats["errors"]:
                                    st.markdown(f"- {err}")
                        
                        # Final verdict
                        if stats["pages_indexed"] == 0:
                            st.warning(f"🔍 No se pudieron indexar páginas. El navegador puede no estar accediendo correctamente al contenido.")
                        else:
                            st.balloons()
                            
                    else:
                        st.error("❌ Error de login a irresistible.church")
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # ============ MAIN CONTENT ============
    
    if "Dashboard" in mode:
        show_dashboard()
    else:
        show_chat(selected_persona, lang_code)

def show_dashboard():
    """Executive Dashboard with metrics and status"""
    st.markdown("""
    <div class="hero-header">
        <h1>📊 Centro de Control</h1>
        <p>Sistema Operativo Iglesia Irresistible</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state.rag.get_stats()}</div>
            <div class="stat-label">📚 Documentos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">6</div>
            <div class="stat-label">👔 Directores</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(DOJO_SCENARIOS)}</div>
            <div class="stat-label">🥋 Escenarios</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        api_status = "✅" if os.environ.get("GOOGLE_API_KEY") else "⚠️"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{api_status}</div>
            <div class="stat-label">🔌 API Status</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🏛️</div>
            <h3>El Gabinete</h3>
            <p>Consulta con 6 directores especializados en diferentes áreas ministeriales.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🥋</div>
            <h3>El Dojo</h3>
            <p>Entrena conversaciones difíciles con simulaciones realistas y evaluación IA.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h3>Base de Conocimiento</h3>
            <p>Sube PDFs, Excel y documentos para que el agente aprenda de tu iglesia.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <h3>Generador de Docs</h3>
            <p>Descarga planes y estrategias en formato Word listo para compartir.</p>
        </div>
        """, unsafe_allow_html=True)

def show_chat(selected_persona, lang_code):
    """Main chat interface"""
    
    # Header based on mode
    if st.session_state.get("dojo_active"):
        st.markdown('<span class="dojo-active">🥋 MODO DOJO ACTIVO</span>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 2.5rem;">💬</div>
            <div>
                <h2 style="margin: 0;">Chat con {selected_persona if selected_persona else 'Agente'}</h2>
                <p style="margin: 0; color: #94a3b8;">Experto en el modelo de Iglesia Irresistible</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Escribe tu mensaje..." if lang_code == "es" else "Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..." if lang_code == "es" else "Thinking..."):
                # Get RAG context
                context = st.session_state.rag.search(prompt)
                
                # Check if Dojo mode
                if st.session_state.get("dojo_active"):
                    scenario_key = st.session_state.get("current_scenario_key", "angry_parent")
                    scenario_root = DOJO_SCENARIOS.get(scenario_key, {})
                    scenario_data = scenario_root.get(lang_code, scenario_root.get("es", {}))
                    
                    response = st.session_state.agent.generate_dojo_response(
                        prompt, 
                        st.session_state.messages,
                        scenario_data
                    )
                else:
                    response = st.session_state.agent.generate_response(
                        prompt,
                        st.session_state.messages,
                        rag_context=context,
                        persona_key=selected_persona
                    )
                
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Download button for conversation
    if st.session_state.messages:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📄 Exportar .docx"):
                docx_bytes = create_docx(st.session_state.messages)
                st.download_button(
                    label="⬇️ Descargar",
                    data=docx_bytes,
                    file_name="conversacion_irresistible.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        with col2:
            if st.button("🗑️ Limpiar Chat"):
                st.session_state.messages = []
                st.session_state.dojo_active = False
                st.rerun()

if __name__ == "__main__":
    main()
