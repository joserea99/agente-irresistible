
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
        # Lazy load heavy/fragile services (Media, RAG) to avoid crashes on init
        self.media_service = None 
        self.rag = None

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
        print(f"🚀 [Research] Starting session for user={user_id} query='{query}'")
        try:
            session_id = str(uuid.uuid4())
            
            # 1. Optimize Query
            print("🔍 [Research] Optimizing query...")
            optimized_query = self.chat_service.optimize_query(query)
            print(f"✅ [Research] Optimized: {query} -> {optimized_query}")
            
            # 2. Find Brandfolder
            print("🔍 [Research] Getting Brandfolders...")
            bfs = self.bf_api.get_brandfolders()
            if not bfs:
                print("❌ [Research] No Brandfolders found")
                raise ValueError("No Brandfolders found")
            bf_id = bfs[0]['id']
            print(f"✅ [Research] Using Brandfolder: {bfs[0].get('attributes', {}).get('name')} ({bf_id})")
            
            # 3. Search Assets
            print(f"🔍 [Research] Searching assets with query: '{optimized_query}'")
            raw_assets = self.bf_api.search_assets(bf_id, optimized_query)
            print(f"✅ [Research] Found {len(raw_assets)} assets with optimized query")
            
            # FALLBACK: If optimized query yields no results, try the original query
            if not raw_assets and query != optimized_query:
                print(f"⚠️ [Research] Optimized query failed. Retrying with raw query: '{query}'")
                raw_assets = self.bf_api.search_assets(bf_id, query)
                print(f"✅ [Research] Found {len(raw_assets)} assets with raw query")

            # FALLBACK 2: If still nothing, try extracting key terms and joining with OR
            if not raw_assets:
                 # Split by space, remove common Spanish stop words
                 stop_words = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'de', 'del', 'a', 'ante', 'bajo', 'con', 'contra', 'de', 'desde', 'en', 'entre', 'hacia', 'hasta', 'para', 'por', 'según', 'sin', 'so', 'sobre', 'tras'}
                 words = [w for w in query.split() if w.lower() not in stop_words and len(w) > 3]
                 
                 if words:
                     or_query = " OR ".join(words)
                     print(f"⚠️ [Research] Retrying with OR keywords: '{or_query}'")
                     raw_assets = self.bf_api.search_assets(bf_id, or_query)
                     print(f"✅ [Research] Found {len(raw_assets)} assets with OR query")

            # FALLBACK 3: Last resort, try just the first significant word
            if not raw_assets and words:
                 simple_query = words[0]
                 print(f"⚠️ [Research] Last resort query: '{simple_query}'")
                 raw_assets = self.bf_api.search_assets(bf_id, simple_query)
                 print(f"✅ [Research] Found {len(raw_assets)} assets with simple query")
            
            # 4. Save Session & Assets Draft
            print(f"💾 [Research] Saving session {session_id} to DB...")
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute("INSERT INTO research_sessions (id, user_id, query, status) VALUES (?, ?, ?, ?)",
                      (session_id, user_id, query, 'proposed'))
            
            proposed_assets = []
            
            print(f"Processing {len(raw_assets)} raw assets...")
            for asset in raw_assets[:100]: # Increased cap from 20 to 100 for deeper research
                info = self.bf_api.extract_asset_info(asset)
                
                # Determine type
                asset_type = 'document'
                url = f"https://brandfolder.com/workbench/{info['id']}" # Default source
                
                # Check for media url
                for att in info['attachments']:
                    mimetype = att.get('mimetype') or ''
                    if 'video' in mimetype:
                        asset_type = 'video'
                        url = att.get('url') # Actual file for transcription later
                        break
                    if 'audio' in mimetype:
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
            print("✅ [Research] Session persisted successfully")
            
            # 5. Generate Semantic Summary
            titles = [a['name'] for a in proposed_assets]
            summary = f"Found {len(titles)} assets related to '{query}'."
            
            return {
                "session_id": session_id,
                "query": query,
                "asset_count": len(proposed_assets),
                "assets": proposed_assets,
                "summary": summary
            }

        except Exception as e:
            print(f"❌ [Research] CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise

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
        row = c.fetchone()
        
        if not row:
            conn.close()
            return None
            
        session = dict(row)
        
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
            # Lazy Init Services
            from .media_service import MediaService
            from .rag_service import RAGManager
            
            if not self.media_service:
                self.media_service = MediaService()
            if not self.rag:
                self.rag = RAGManager()

            try:
                # 1. Transcribe if media
                content = f"Asset: {asset['name']}\nType: {asset['type']}"
                
                if asset['type'] in ['video', 'audio']:
                    # REFRESH URL: Stored URL might be expired signed URL
                    try:
                        fresh_details = self.bf_api.get_asset_details(asset['asset_id'])
                        fresh_info = self.bf_api.extract_asset_info(fresh_details)
                        
                        fresh_url = None
                        for att in fresh_info['attachments']:
                             mimetype = att.get('mimetype') or ''
                             if asset['type'] == 'video' and 'video' in mimetype:
                                 fresh_url = att.get('url')
                                 break
                             if asset['type'] == 'audio' and 'audio' in mimetype:
                                 fresh_url = att.get('url')
                                 break
                        
                        if fresh_url and fresh_url.startswith('http'):
                            local_path = self.bf_api.download_attachment(fresh_url)
                            if local_path:
                                transcript = self.media_service.transcribe_media(local_path, mime_type='video/mp4' if asset['type']=='video' else 'audio/mp3')
                                content += f"\n\n--- TRANSCRIPT ---\n{transcript}"
                                os.remove(local_path)
                    except Exception as e:
                        print(f"⚠️ Failed to refresh/download media {asset['id']}: {e}")
                        # Don't fail the whole asset logic, just skip transcript
                        content += f"\n\n[Transcription Failed: {e}]"
                
                # 2. Index to Chroma
                # Source needs to be the clickable link
                source_link = f"https://brandfolder.com/workbench/{asset['asset_id']}"
                self.rag.add_document(content, source_link, title=asset['name'])
                
                # 3. Update Status
                c.execute("UPDATE research_assets SET status='indexed' WHERE id=?", (asset['id'],))
                conn.commit()
                stats["indexed"] += 1
                print(f"✅ [Research] Asset {asset['id']} ({asset['name']}) indexed & saved.")
                
            except Exception as e:
                print(f"Failed asset {asset['id']}: {e}")
                c.execute("UPDATE research_assets SET status='error' WHERE id=?", (asset['id'],))
                conn.commit()
                stats["failed"] += 1
                
        c.execute("UPDATE research_sessions SET status='completed' WHERE id=?", (session_id,))
        conn.commit()
        conn.close()
        
        return stats
