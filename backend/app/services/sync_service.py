"""
sync_service.py - Automated Full-Library Ingestion
Periodically scans the Brandfolder and indexes ALL content into the agent's memory.

Features:
  - Differential sync: Only ingests content NOT already in the vector database.
  - No duplication: Checks both the local SQLite research_assets table and the
    Supabase documents table before processing any asset.
  - Lockout: Prevents two concurrent syncs from running at the same time.
  - Preserves existing memory: Never deletes or overwrites existing indexed content.
"""

import sqlite3
import os
import uuid
from datetime import datetime

# DB Path (same as research_service.py)
if os.path.exists("/app/brain_data"):
    DB_PATH = "/app/brain_data/irresistible_app.db"
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.abspath(os.path.join(current_dir, "../../..", "irresistible_app.db"))

# Lock flag to prevent concurrent runs
_sync_running = False


def _init_sync_log_table():
    """Ensures the sync_log table exists for tracking sync history."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT DEFAULT 'running',   -- running, completed, failed
            total_found INTEGER DEFAULT 0,
            new_indexed INTEGER DEFAULT 0,
            skipped INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()


def _asset_already_indexed(c, asset_id: str) -> bool:
    """
    Checks if an asset has already been successfully processed.
    Uses the local research_assets table as a fast first-level check.
    """
    c.execute(
        "SELECT id FROM research_assets WHERE asset_id=? AND status='indexed' LIMIT 1",
        (asset_id,)
    )
    return c.fetchone() is not None


def full_sync():
    """
    Main sync function. Scans ALL assets in Brandfolder and indexes any
    content not already present in the vector database.

    This function is safe to call multiple times:
    - It will skip assets already indexed.
    - It will not delete or modify existing indexed content.
    - It will not run if a sync is already in progress.
    """
    global _sync_running

    if _sync_running:
        print("⏳ [AutoSync] Sync already running. Skipping this trigger.")
        return

    _sync_running = True
    _init_sync_log_table()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create a log entry for this sync run
    c.execute(
        "INSERT INTO sync_log (status) VALUES ('running')"
    )
    conn.commit()
    log_id = c.lastrowid
    started_at = datetime.utcnow()

    stats = {"total_found": 0, "new_indexed": 0, "skipped": 0, "failed": 0}

    try:
        from .brandfolder_service import BrandfolderAPI
        from .media_service import MediaService
        from .rag_service import RAGManager

        print("🔄 [AutoSync] Starting full library sync...")

        bf_api = BrandfolderAPI()
        rag = RAGManager()

        # 1. Get all Brandfolders
        brandfolders = bf_api.get_brandfolders()
        if not brandfolders:
            raise ValueError("No Brandfolders accessible.")
        bf_id = brandfolders[0]["id"]
        print(f"📚 [AutoSync] Using Brandfolder: {brandfolders[0].get('attributes', {}).get('name')} ({bf_id})")

        # 2. Get ALL assets (paginated, no search filter)
        print("🔍 [AutoSync] Fetching all assets from Brandfolder...")
        raw_assets = bf_api.get_assets(brandfolder_id=bf_id, per_page=100)
        stats["total_found"] = len(raw_assets)
        print(f"✅ [AutoSync] Found {len(raw_assets)} total assets in library.")

        # Update log with total count
        c.execute(
            "UPDATE sync_log SET total_found=? WHERE id=?",
            (stats["total_found"], log_id)
        )
        conn.commit()

        # 3. Create a special auto-sync session in research_sessions
        session_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO research_sessions (id, user_id, query, status) VALUES (?, ?, ?, ?)",
            (session_id, "system_auto_sync", f"[AutoSync] {started_at.isoformat()}", "processing")
        )
        conn.commit()

        media_service = MediaService()

        # 4. Process each asset — skip ones already indexed
        for asset in raw_assets:
            info = bf_api.extract_asset_info(asset)
            asset_id = info["id"]
            name = info["name"]

            # --- DEDUPLICATION CHECK 1: Local SQLite ---
            if _asset_already_indexed(c, asset_id):
                print(f"⏭️  [AutoSync] Skipping (already indexed): {name}")
                stats["skipped"] += 1
                continue

            # Determine asset type & URL
            asset_type = "document"
            url = f"https://brandfolder.com/workbench/{asset_id}"

            for att in info["attachments"]:
                mimetype = att.get("mimetype") or ""
                if "video" in mimetype:
                    asset_type = "video"
                    url = att.get("url")
                    break
                if "audio" in mimetype:
                    asset_type = "audio"
                    url = att.get("url")
                    break

            source_link = f"https://brandfolder.com/workbench/{asset_id}"

            # --- DEDUPLICATION CHECK 2: Supabase Vector DB ---
            if rag.document_exists(source_link):
                print(f"⏭️  [AutoSync] Skipping (already in vector DB): {name}")
                # Mark as indexed in SQLite so future syncs are faster
                c.execute(
                    "INSERT OR IGNORE INTO research_assets (session_id, asset_id, name, type, url, status) VALUES (?,?,?,?,?,?)",
                    (session_id, asset_id, name, asset_type, url, "indexed")
                )
                conn.commit()
                stats["skipped"] += 1
                continue

            # --- PROCESS NEW ASSET ---
            try:
                # Insert into DB with 'pending' status first
                c.execute(
                    "INSERT INTO research_assets (session_id, asset_id, name, type, url, status) VALUES (?,?,?,?,?,?)",
                    (session_id, asset_id, name, asset_type, url, "pending")
                )
                conn.commit()
                asset_row_id = c.lastrowid

                content = f"Asset: {name}\nType: {asset_type}"

                if asset_type in ["video", "audio", "document"]:
                    try:
                        fresh_details = bf_api.get_asset_details(asset_id)
                        fresh_info = bf_api.extract_asset_info(fresh_details)

                        fresh_url = None
                        for att in fresh_info["attachments"]:
                            mimetype = att.get("mimetype") or ""
                            if asset_type == "video" and "video" in mimetype:
                                fresh_url = att.get("url")
                                break
                            if asset_type == "audio" and "audio" in mimetype:
                                fresh_url = att.get("url")
                                break
                            if asset_type == "document" and any(x in mimetype for x in ["pdf", "document", "text"]):
                                fresh_url = att.get("url")
                                break

                        # Fallback to first attachment for documents
                        if not fresh_url and asset_type == "document" and fresh_info["attachments"]:
                            fresh_url = fresh_info["attachments"][0].get("url")

                        if fresh_url and fresh_url.startswith("http"):
                            local_path = bf_api.download_attachment(fresh_url)
                            if local_path:
                                if asset_type in ["video", "audio"]:
                                    mime = "video/mp4" if asset_type == "video" else "audio/mp3"
                                    transcript = media_service.transcribe_media(local_path, mime_type=mime)
                                    content += f"\n\n--- TRANSCRIPT ---\n{transcript}"
                                elif asset_type == "document":
                                    import pypdf
                                    try:
                                        reader = pypdf.PdfReader(local_path)
                                        pdf_text = ""
                                        for page in reader.pages:
                                            extracted = page.extract_text()
                                            if extracted:
                                                pdf_text += extracted + "\n"
                                        if pdf_text.strip():
                                            content += f"\n\n--- DOCUMENT TEXT ---\n{pdf_text}"
                                    except Exception as e:
                                        print(f"⚠️  PDF parse error for {name}: {e}")
                                os.remove(local_path)
                    except Exception as e:
                        print(f"⚠️  [AutoSync] Media processing failed for {name}: {e}")
                        content += f"\n\n[Extraction Failed: {e}]"

                # Index to Vector DB
                rag.add_document(content, source_link, title=name)

                # Mark as indexed in DB
                c.execute(
                    "UPDATE research_assets SET status='indexed', content=? WHERE id=?",
                    (content, asset_row_id)
                )
                conn.commit()
                stats["new_indexed"] += 1
                print(f"✅ [AutoSync] Indexed: {name}")

            except Exception as e:
                print(f"❌ [AutoSync] Failed to process {name}: {e}")
                stats["failed"] += 1

        # 5. Mark session and log as completed
        c.execute("UPDATE research_sessions SET status='completed' WHERE id=?", (session_id,))
        c.execute(
            """UPDATE sync_log 
               SET status='completed', completed_at=CURRENT_TIMESTAMP,
                   new_indexed=?, skipped=?, failed=?
               WHERE id=?""",
            (stats["new_indexed"], stats["skipped"], stats["failed"], log_id)
        )
        conn.commit()
        print(
            f"🎉 [AutoSync] Sync complete! New: {stats['new_indexed']} | "
            f"Skipped: {stats['skipped']} | Failed: {stats['failed']}"
        )

    except Exception as e:
        print(f"💥 [AutoSync] CRITICAL ERROR: {e}")
        c.execute(
            "UPDATE sync_log SET status='failed', completed_at=CURRENT_TIMESTAMP, notes=? WHERE id=?",
            (str(e), log_id)
        )
        conn.commit()

    finally:
        conn.close()
        _sync_running = False


def get_last_sync_status() -> dict:
    """Returns the status of the last completed or running sync."""
    _init_sync_log_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {"status": "never_run"}
