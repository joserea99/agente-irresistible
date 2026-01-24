
import sqlite3
import os
import json
import uuid
from datetime import datetime
from .brandfolder_service import BrandfolderAPI
from .chat_service import ChatService
from .media_service import MediaService
from .rag_service import RAGManager

# DB Path (Same volume as auth DB)
# In Railway with a Volume mounted at /app/brain_data
if os.path.exists("/app/brain_data"):
    DB_PATH = "/app/brain_data/irresistible_app.db"
    print(f"📂 Using Persistent DB at: {DB_PATH}")
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.abspath(os.path.join(current_dir, "../../..", "irresistible_app.db"))
    print(f"📂 Using Local DB at: {DB_PATH}")

class ResearchService:
    def __init__(self):
        self._init_db()
        self.bf_api = BrandfolderAPI()
        self.chat_service = ChatService()
        self.media_service = MediaService()
        self.rag = RAGManager()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Sessions: The high level research task
        c.execute('''
            CREATE TABLE IF NOT EXISTS research_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                query TEXT,
                status TEXT DEFAULT 'proposed', -- proposed, processing, completed, failed
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Assets: The items found in a session
        c.execute('''
            CREATE TABLE IF NOT EXISTS research_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                asset_id TEXT,
                name TEXT,
                type TEXT, -- video, audio, image, document
                url TEXT,
                status TEXT DEFAULT 'pending', -- pending, transcribed, indexed, error
                FOREIGN KEY (session_id) REFERENCES research_sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_session(self, user_id: str, query: str) -> dict:
        """
        Step 1: Scan & Map.
        Searches Brandfolder, clusters results, and saves a proposed session.
        """
        session_id = str(uuid.uuid4())
        
        # 1. Optimize Query
        optimized_query = self.chat_service.optimize_query(query)
        print(f"🔍 Researching: {query} -> {optimized_query}")
        
        # 2. Scan Brandfolder (Limit scan to top 20 for Proposal speed)
        # In a real app we might want to scan more, but for speed let's stick to 20
        # We assume the first Brandfolder available
        bfs = self.bf_api.get_brandfolders()
        if not bfs:
            raise ValueError("No Brandfolders found")
        bf_id = bfs[0]['id']
        
        raw_assets = self.bf_api.search_assets(bf_id, optimized_query)
        
        # FALLBACK: If optimized query yields no results, try the original query
        if not raw_assets and query != optimized_query:
            print(f"⚠️ Optimized query returned 0 results. Retrying with raw query: '{query}'")
            raw_assets = self.bf_api.search_assets(bf_id, query)

        # FALLBACK 2: If still nothing, try a very broad search (first word)
        if not raw_assets and len(query.split()) > 1:
             simple_query = query.split()[0]
             print(f"⚠️ Raw query returned 0 results. Retrying with simple query: '{simple_query}'")
             raw_assets = self.bf_api.search_assets(bf_id, simple_query)
        
        # 3. Save Session & Assets Draft
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("INSERT INTO research_sessions (id, user_id, query, status) VALUES (?, ?, ?, ?)",
                  (session_id, user_id, query, 'proposed'))
        
        proposed_assets = []
        
        for asset in raw_assets[:20]: # Cap at 20 for proposal
            info = self.bf_api.extract_asset_info(asset)
            
            # Determine type
            asset_type = 'document'
            url = f"https://brandfolder.com/workbench/{info['id']}" # Default source
            
            # Check for media url
            for att in info['attachments']:
                if 'video' in att.get('mimetype', ''):
                    asset_type = 'video'
                    url = att.get('url') # Actual file for transcription later
                    break
                if 'audio' in att.get('mimetype', ''):
                    asset_type = 'audio'
                    url = att.get('url')
                    break
            
            c.execute("INSERT INTO research_assets (session_id, asset_id, name, type, url) VALUES (?, ?, ?, ?, ?)",
                      (session_id, info['id'], info['name'], asset_type, url))
            
            proposed_assets.append({
                "id": info['id'],
                "name": info['name'],
                "type": asset_type
            })
            
        conn.commit()
        conn.close()
        
        # 4. Generate Semantic Summary of what was found
        # We simply list the titles to Gemini to categorize them
        titles = [a['name'] for a in proposed_assets]
        summary = f"Found {len(titles)} assets related to '{query}'."
        
        return {
            "session_id": session_id,
            "query": query,
            "asset_count": len(proposed_assets),
            "assets": proposed_assets,
            "summary": summary
        }

    def get_history(self, user_id: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM research_sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_session_status(self, session_id: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM research_sessions WHERE id=?", (session_id,))
        session = dict(c.fetchone())
        
        c.execute("SELECT * FROM research_assets WHERE session_id=?", (session_id,))
        assets = [dict(r) for r in c.fetchall()]
        
        conn.close()
        return {**session, "assets": assets}

    def execute_session(self, session_id: str):
        """
        Step 2: Execute.
        Runs through the assets, transcribes media, and indexes logic.
        NOTE: This should ideally be a background task (Celery/RQ), but we'll do sync generator or background thread for simplicity in this MVP.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("UPDATE research_sessions SET status='processing' WHERE id=?", (session_id,))
        conn.commit()
        
        c.execute("SELECT * FROM research_assets WHERE session_id=?", (session_id,))
        assets = [dict(r) for r in c.fetchall()]
        
        # We define a generator to yield progress if called via StreamingResponse, 
        # or we just process and user polls status. Let's do polling update for simplicity.
        
        stats = {"indexed": 0, "failed": 0}
        
        for asset in assets:
            try:
                # 1. Transcribe if media
                content = f"Asset: {asset['name']}\nType: {asset['type']}"
                
                if asset['type'] in ['video', 'audio'] and asset['url'].startswith('http'):
                    # Download & Transcribe
                    # Note: We need to re-instantiate API inside here or pass it? API is stateless mostly.
                    # Use existing downloading logic from BrandfolderAPI? 
                    # Simpler: use requests directly or duplicate logic slightly to avoid circular dependency messy refactor
                    local_path = self.bf_api.download_attachment(asset['url'])
                    if local_path:
                        transcript = self.media_service.transcribe_media(local_path, mime_type='video/mp4' if asset['type']=='video' else 'audio/mp3')
                        content += f"\n\n--- TRANSCRIPT ---\n{transcript}"
                        os.remove(local_path)
                
                # 2. Index to Chroma
                # Source needs to be the clickable link
                source_link = f"https://brandfolder.com/workbench/{asset['asset_id']}"
                self.rag.add_document(content, source_link, title=asset['name'])
                
                # 3. Update Status
                c.execute("UPDATE research_assets SET status='indexed' WHERE id=?", (asset['id'],))
                conn.commit()
                stats["indexed"] += 1
                
            except Exception as e:
                print(f"Failed asset {asset['id']}: {e}")
                c.execute("UPDATE research_assets SET status='error' WHERE id=?", (asset['id'],))
                conn.commit()
                stats["failed"] += 1
                
        c.execute("UPDATE research_sessions SET status='completed' WHERE id=?", (session_id,))
        conn.commit()
        conn.close()
        
        return stats
