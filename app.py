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
        
        # ========== SMART CRAWL (API-BASED) ==========
        st.divider()
        st.markdown("### 🧠 Smart Learning")
        st.caption("Aprende directamente de Brandfolder via API - Sin límites de navegador")
        
        # Check for API key
        brandfolder_api_key = os.environ.get("BRANDFOLDER_API_KEY", "")
        
        # Allow user to input API key if not in environment
        if not brandfolder_api_key:
            st.warning("⚠️ API Key de Brandfolder no configurada")
            brandfolder_api_key = st.text_input(
                "🔑 Ingresa tu API Key de Brandfolder",
                type="password",
                help="Obtén tu API key en: https://brandfolder.com/profile#integrations"
            )
        
        if brandfolder_api_key:
            # Topic input for search/prioritization
            search_topic = st.text_input(
                "🎯 ¿Qué tema quieres aprender?",
                placeholder="Ej: Neighborhood to Kitchen, grupos pequeños, liderazgo...",
                key="api_crawl_topic",
                help="Busca assets específicos o deja vacío para traer todo"
            )
            
            # Options
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                include_descriptions = st.checkbox("📝 Indexar descripciones", value=True)
            with col_opt2:
                auto_transcribe = st.checkbox("🎬 Auto-transcribir media", value=False, 
                    help="Transcribe videos/audios automáticamente (puede tomar tiempo)")
            
            max_assets = st.slider("Máximo de assets a procesar", 10, 200, 50, key="max_api_assets")
            
            if st.button("🚀 Iniciar Aprendizaje via API", use_container_width=True):
                try:
                    from brandfolder_api import BrandfolderAPI, test_connection
                    
                    # Progress containers
                    progress_bar = st.progress(0)
                    log_area = st.empty()
                    
                    log_area.markdown("🔌 Conectando a Brandfolder API...")
                    
                    # Test connection first
                    connection = test_connection(brandfolder_api_key)
                    
                    if not connection["success"]:
                        st.error(f"❌ {connection['message']}")
                    else:
                        st.success(connection["message"])
                        
                        api = BrandfolderAPI(brandfolder_api_key)
                        
                        # Find the irresistible church brandfolder
                        brandfolders = connection["brandfolders"]
                        target_bf = None
                        
                        for bf in brandfolders:
                            if "irresistible" in bf["name"].lower() or "irresistible" in bf.get("slug", "").lower():
                                target_bf = bf
                                break
                        
                        if not target_bf and brandfolders:
                            target_bf = brandfolders[0]  # Use first available
                        
                        if not target_bf:
                            st.error("❌ No se encontraron brandfolders accesibles")
                        else:
                            st.info(f"📂 Brandfolder: **{target_bf['name']}**")
                            log_area.markdown(f"📂 Usando brandfolder: {target_bf['name']}")
                            
                            # Get content
                            log_area.markdown("📥 Obteniendo assets...")
                            
                            if search_topic:
                                assets = api.search_assets(target_bf["id"], search_topic)
                                log_area.markdown(f"🔍 Búsqueda: '{search_topic}' - {len(assets)} resultados")
                            else:
                                assets = api.get_assets(brandfolder_id=target_bf["id"])
                                log_area.markdown(f"📚 Cargando todos los assets: {len(assets)} encontrados")
                            
                            # Limit assets
                            assets = assets[:max_assets]
                            
                            # Process assets
                            stats = {
                                "total": len(assets),
                                "indexed": 0,
                                "videos": [],
                                "audios": [],
                                "documents": [],
                                "errors": []
                            }
                            
                            indexed_items = []
                            
                            for idx, asset in enumerate(assets):
                                try:
                                    info = api.extract_asset_info(asset)
                                    name = info.get("name", "Untitled")
                                    description = info.get("description", "")
                                    ext = (info.get("extension") or "").lower()
                                    
                                    progress_bar.progress((idx + 1) / len(assets))
                                    log_area.markdown(f"📄 **[{idx+1}/{len(assets)}]** Procesando: {name[:40]}...")
                                    
                                    # Categorize by type
                                    if ext in ["mp4", "mov", "avi", "webm"]:
                                        stats["videos"].append(info)
                                    elif ext in ["mp3", "wav", "m4a", "ogg"]:
                                        stats["audios"].append(info)
                                    elif ext in ["pdf", "doc", "docx", "ppt", "pptx"]:
                                        stats["documents"].append(info)
                                    
                                    # Index to knowledge base
                                    if include_descriptions and (name or description):
                                        content = f"ASSET: {name}\n"
                                        if description:
                                            content += f"DESCRIPCIÓN: {description}\n"
                                        content += f"TIPO: {ext or 'desconocido'}\n"
                                        
                                        # Add attachment info
                                        for att in info.get("attachments", []):
                                            content += f"ARCHIVO: {att.get('filename', 'unknown')}\n"
                                            if att.get('url'):
                                                content += f"URL: {att['url']}\n"
                                        
                                        st.session_state.rag.add_document(
                                            content=content,
                                            source_url=f"brandfolder://{target_bf['id']}/{info['id']}",
                                            title=name
                                        )
                                        stats["indexed"] += 1
                                        indexed_items.append({"name": name, "type": ext})
                                        log_area.markdown(f"✅ Indexado: {name[:40]}")
                                        
                                except Exception as e:
                                    stats["errors"].append(f"{name}: {str(e)[:50]}")
                            
                            progress_bar.progress(1.0)
                            
                            # ===== LEARNING REPORT =====
                            st.markdown("---")
                            st.markdown("## 🧠 Reporte de Aprendizaje")
                            st.success(f"✅ **¡Completado!** Se indexaron {stats['indexed']} assets a la base de conocimiento.")
                            
                            # Stats
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("📊 Total Assets", stats["total"])
                            with col2:
                                st.metric("📚 Indexados", stats["indexed"])
                            with col3:
                                st.metric("🎬 Videos", len(stats["videos"]))
                            with col4:
                                st.metric("📄 Docs", len(stats["documents"]))
                            
                            # Media found
                            if stats["videos"] or stats["audios"]:
                                st.markdown("### 🎬 Multimedia Encontrada")
                                
                                if stats["videos"]:
                                    with st.expander(f"🎬 Videos ({len(stats['videos'])})"):
                                        for v in stats["videos"][:20]:
                                            st.markdown(f"- **{v['name']}**")
                                            for att in v.get("attachments", []):
                                                if att.get("url"):
                                                    st.caption(f"  📎 {att.get('filename', 'file')}")
                                
                                if stats["audios"]:
                                    with st.expander(f"🎧 Audios ({len(stats['audios'])})"):
                                        for a in stats["audios"][:20]:
                                            st.markdown(f"- **{a['name']}**")
                                
                                # Store for transcription
                                st.session_state["api_found_media"] = {
                                    "videos": stats["videos"],
                                    "audios": stats["audios"]
                                }
                                
                                # Transcription button
                                if stats["videos"] or stats["audios"]:
                                    st.markdown("### 🎧 Transcripción de Multimedia")
                                    total_media = len(stats["videos"]) + len(stats["audios"])
                                    st.info(f"📝 {total_media} archivos multimedia disponibles para transcripción")
                                    
                                    if st.button("🚀 Transcribir Multimedia", key="api_transcribe_btn"):
                                        trans_progress = st.progress(0)
                                        trans_log = st.empty()
                                        transcribed = 0
                                        
                                        all_media = stats["videos"][:5] + stats["audios"][:5]
                                        
                                        for i, media in enumerate(all_media):
                                            trans_log.markdown(f"🎬 Procesando: {media['name'][:40]}...")
                                            
                                            for att in media.get("attachments", []):
                                                att_url = att.get("url")
                                                if att_url:
                                                    try:
                                                        # Download and transcribe
                                                        local_path = api.download_attachment(att_url)
                                                        if local_path:
                                                            transcript = process_media_url(local_path)
                                                            if transcript and "Error" not in transcript:
                                                                st.session_state.rag.add_document(
                                                                    content=f"TRANSCRIPCIÓN: {media['name']}\n\n{transcript}",
                                                                    source_url=att_url,
                                                                    title=f"Transcripción: {media['name']}"
                                                                )
                                                                transcribed += 1
                                                                trans_log.markdown(f"✅ Transcrito: {media['name'][:40]}")
                                                            # Clean up
                                                            os.remove(local_path)
                                                    except Exception as e:
                                                        trans_log.markdown(f"⚠️ Error: {str(e)[:40]}")
                                            
                                            trans_progress.progress((i + 1) / len(all_media))
                                        
                                        trans_progress.progress(1.0)
                                        st.success(f"🎉 ¡Transcripción completada! {transcribed} archivos procesados.")
                                        st.balloons()
                            
                            # Documents
                            if stats["documents"]:
                                with st.expander(f"📄 Documentos ({len(stats['documents'])})"):
                                    for d in stats["documents"][:20]:
                                        st.markdown(f"- **{d['name']}** (.{d.get('extension', '?')})")
                            
                            # Indexed items
                            if indexed_items:
                                with st.expander(f"📚 Items Indexados ({len(indexed_items)})"):
                                    for item in indexed_items[:30]:
                                        st.markdown(f"- {item['name'][:50]} ({item['type']})")
                            
                            # Errors
                            if stats["errors"]:
                                with st.expander(f"⚠️ Errores ({len(stats['errors'])})"):
                                    for err in stats["errors"]:
                                        st.markdown(f"- {err}")
                            
                            st.balloons()
                            
                except ImportError:
                    st.error("❌ Error: brandfolder_api.py no encontrado. Contacta al administrador.")
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
