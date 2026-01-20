import streamlit as st
import time
from database import verify_user, add_user, save_message, get_chat_history, init_db
from agent_logic import AgentEngine
from rag_manager import RAGManager
from browser_service import BrowserService
from personas import PERSONAS
from dojo_scenarios import DOJO_SCENARIOS
from utils import create_docx
from dotenv import load_dotenv

load_dotenv()

# Initialize components
if "agent" not in st.session_state:
    st.session_state.agent = AgentEngine()
    
if "rag" not in st.session_state:
    st.session_state.rag = RAGManager()

def main():
    st.set_page_config(page_title="Irresistible Team Agent", page_icon="⛪", layout="wide")
    
    # Simple Session State for Auth
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        login_page()
    else:
        dashboard()

def login_page():
    st.title("🔐 Irresistible Team Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = verify_user(username, password)
            if user:
                st.session_state.user = {"username": username, "name": user[0], "role": user[1]}
                st.success(f"Welcome back, {user[0]}!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("New Email", key="reg_email")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        new_name = st.text_input("Full Name", key="reg_name")
        if st.button("Create Account"):
            if add_user(new_user, new_pass, new_name):
                st.success("Account created! Please login.")
            else:
                st.error("User already exists.")

def dashboard():
    user = st.session_state.user
    
    # Sidebar
    with st.sidebar:
        st.header(f"👤 {user['name']}")
        st.caption(f"Role: {user['role']}")
        
        st.divider()
        # Language Selector
        cols = st.columns(2)
        with cols[0]:
            st.write("🌐 Language:")
        with cols[1]:
            language = st.selectbox("Lang", ["Español", "English"], label_visibility="collapsed")
        
        lang_code = "es" if language == "Español" else "en"
        
        st.divider()
        mode = st.radio("Mode / Modo:", ["Consultant / Gabinete", "The Dojo (Roleplay)"])
        
        selected_persona = None
        selected_scenario = None
        
        if "Consultant" in mode:
            st.subheader("🏛️ The Cabinet")
            selected_persona = st.selectbox(
                "Select Director / Director:",
                options=list(PERSONAS.keys()),
                index=0
            )
            st.caption(f"Talking to: **{selected_persona}**")
        else:
            st.subheader("🥋 The Dojo")
            st.info("Train your leadership skills / Entrena tu liderazgo.")
            
            # Show scenario keys provided in the dictionary
            scenario_key = st.selectbox(
                "Choose Scenario / Escenario:",
                options=list(DOJO_SCENARIOS.keys())
            )
            
            if st.button("Start Simulation"):
                st.session_state.messages = []
                
                # Fetch localized content
                scenario_root = DOJO_SCENARIOS[scenario_key]
                scenario_data = scenario_root.get(lang_code, scenario_root["es"])
                
                # Inject opening line
                st.session_state.messages.append({"role": "assistant", "content": f"**[ROLE: {scenario_data['name']}]**\n\n" + scenario_data["opening_line"]})
                st.session_state.dojo_active = True
                st.session_state.current_scenario_key = scenario_key # Store the key to lookup later
                st.session_state.current_lang_code = lang_code
                st.rerun()

            if st.button("End & Evaluate"):
                if st.session_state.get("dojo_active"):
                    eval_result = st.session_state.agent.evaluate_dojo_performance(
                        st.session_state.messages, 
                        st.session_state.current_scenario_key, # Passing just name for context
                        language=st.session_state.get("current_lang_code", "es")
                    )
                    st.session_state.messages.append({"role": "assistant", "content": f"**🥋 DOJO EVALUATION:**\n\n{eval_result}"})
                    st.session_state.dojo_active = False
                    st.rerun()

        if st.button("Log Out"):
            st.session_state.user = None
            st.rerun()
            
        if st.button("🕷️ Smart Crawl (Deep)"):
            with st.spinner("🕷️ Crawling recursively... This may take a while."):
                browser = BrowserService()
                # Start from the dashboard or a known useful root
                start_url = "https://my.irresistible.church/irresistiblechurchnetwork"
                pages = browser.crawl_recursive(start_url, max_depth=2, max_pages=15)
                browser.close()
                
                count = 0
                for p in pages:
                    if p['content']:
                        st.session_state.rag.add_document(
                            content=p['content'],
                            source_url=p['url'],
                            title=p['title']
                        )
                        count += 1
                
                st.success(f"Successfully indexed {count} pages from deep crawl!")
                
                # --- PROCESS FOUND MEDIA ---
                media_queue = []
                for p in pages:
                    if p.get('media_links'):
                        media_queue.extend(p['media_links'])
                
                # Deduplicate
                media_queue = list(set(media_queue))
                
                if media_queue:
                    st.divider()
                    st.info(f"📹 Found {len(media_queue)} media files. Transcribing...")
                    progress_bar = st.progress(0)
                    
                    # We need cookies from the browser session for authenticated downloads
                    # For now, we'll try without, but ideally we pass them.
                    # The browser service closed, so cookies are gone unless we saved them.
                    # Let's hope the links are signed URLs (GCS usually are).
                    
                    from media_processor import process_media_url
                    
                    for idx, m_url in enumerate(media_queue):
                        with st.spinner(f"🎧 Transcribing: {m_url.split('/')[-1]}..."):
                            transcript = process_media_url(m_url)
                            
                            if transcript and "Error" not in transcript:
                                st.session_state.rag.add_document(
                                    content=f"TRANSCRIPT OF {m_url}:\n\n{transcript}",
                                    source_url=m_url,
                                    title=f"Media: {m_url.split('/')[-1]}"
                                )
                                st.write(f"✅ Indexed: {m_url.split('/')[-1]}")
                            else:
                                st.error(f"Failed: {m_url} - {transcript}")
                        
                        progress_bar.progress((idx + 1) / len(media_queue))
                
        st.divider()
        st.subheader("📄 Upload Knowledge (PDF / Excel)")
        uploaded_file = st.file_uploader("Upload: Manuals (PDF) or Budgets/Lists (Excel)", type=["pdf", "xlsx", "csv", "txt"])
        
        if uploaded_file is not None:
            if st.button("Process File"):
                with st.spinner("Analyzing file content..."):
                    try:
                        text = ""
                        file_type = uploaded_file.name.split(".")[-1].lower()
                        
                        # PDF Handler
                        if file_type == "pdf":
                            import pypdf
                            reader = pypdf.PdfReader(uploaded_file)
                            for page in reader.pages:
                                text += page.extract_text() + "\n"
                        
                        # EXCEL/CSV Handler
                        elif file_type in ["xlsx", "csv"]:
                            import pandas as pd
                            if file_type == "xlsx":
                                df = pd.read_excel(uploaded_file)
                            else:
                                df = pd.read_csv(uploaded_file)
                            
                            # Convert to text representation (limit generic large files)
                            text = df.to_string(index=False)
                            st.info(f"Read {len(df)} rows from spreadsheet.")
                        
                        # TEXT Handler
                        elif file_type == "txt":
                            text = uploaded_file.read().decode("utf-8")
                        
                        if text:
                            st.session_state.rag.add_document(
                                content=text,
                                source_url=uploaded_file.name,
                                title=f"File: {uploaded_file.name}"
                            )
                            st.success(f"Successfully indexed '{uploaded_file.name}'!")
                        else:
                            st.warning("No readable text found.")
                            
                    except Exception as e:
                        st.error(f"Error processing file: {e}")
                
        st.divider()
        st.subheader("🧠 Knowledge Base")
        stats = st.session_state.rag.get_stats()
        st.metric("Indexed Docs", stats)
        
        st.divider()
        st.info("🔧 Tools")
        if st.button("Learn from Dashboard"):
            with st.spinner("Agent is navigating to dashboard..."):
                browser = BrowserService()
                # Try to login first to ensure state is fresh
                browser.login("jose.rea@lbne.org", "jajciX-pohto7-dyd")
                
                # Scrape main dashboard
                data, err = browser.get_page_content() # Use generic fetch since we are already authenticated from login() call or cache
                # Actually, login() stays on page.
                
                # Check media service for scraping
                # We need to manually invoke crawl or scrape logic
                # Let's just do a specific dashboard crawl
                start_url = "https://my.irresistible.church/irresistiblechurchnetwork"
                # browser.page is active
                browser.page.goto(start_url)
                data = browser.get_page_content() # This now returns media_links too!
                
                if data:
                     # Add Text
                    count = st.session_state.rag.add_document(data["content"], data["url"], data["title"])
                    st.success(f"Learned from Dashboard! Media links found: {len(data.get('media_links', []))}")
                    
                    # Add Media (Quick Add)
                    if data.get('media_links'):
                        st.session_state.rag.add_document(
                            content=f"Found Media Links on Dashboard: {', '.join(data['media_links'])}",
                            source_url=data['url'],
                            title="Deshboard Media Index"
                        )
                else:
                    st.error("Failed to scrape dashboard.")
                browser.close()

    # Main Chat Interface
    st.title("💬 Irresistible Bot")
    st.caption("Experto en el modelo de Iglesia Irresistible")

    # Load History
    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Load history from DB only once at the start if needed
        db_history = get_chat_history(user["username"])
        for msg in db_history:
            st.session_state.messages.append({"role": msg["role"], "content": msg["content"]})
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat logic
    if prompt := st.chat_input("Pregunta sobre la estrategia de Iglesia Irresistible..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message(user["username"], "user", prompt) # Save to DB

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Generate and display AI response
        with st.chat_message("assistant"):
            # Agent decides if it needs to search or browse
            # Determine if we are in Dojo Mode
            if "The Dojo" in mode and st.session_state.get("dojo_active"):
                # Get the stored scenario key and lang
                scen_key = st.session_state.get("current_scenario_key")
                lang = st.session_state.get("current_lang_code", "es")
                
                scenario_root = DOJO_SCENARIOS[scen_key]
                scenario_data = scenario_root.get(lang, scenario_root["es"])
                
                response = st.session_state.agent.generate_response(
                    user_input=prompt,
                    history=st.session_state.messages,
                    system_prompt_override=scenario_data["system_prompt"]
                )
            else:
                response = st.session_state.agent.generate_response(
                    user_input=prompt, 
                    history=st.session_state.messages,
                    persona_key=selected_persona
                )
            st.markdown(response)
        
        save_message(user["username"], "assistant", response)
        
        # --- DOCUMENT EXPORT ---
        # We generate the file in memory
        docx_file = create_docx(response, title=f"Guide: {prompt[:30]}...")
        
        st.download_button(
            label="📄 Download Guide (Word)",
            data=docx_file,
            file_name="irresistible_guide.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )


if __name__ == "__main__":
    init_db()
    main()
