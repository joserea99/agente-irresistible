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


def _clean_html(text: str) -> str:
    """Strip HTML tags from an asset description (Brandfolder stores rich HTML)."""
    if not text:
        return ""
    if "<" not in text:
        return text.strip()
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    except Exception:
        return text.strip()


def extract_text_from_document(path: str, mimetype: str = "") -> str:
    """
    Extract text from a downloaded document, dispatching by type:
    PDF (pypdf), Word .docx (python-docx), PowerPoint .pptx (python-pptx),
    or plain text/markdown/csv. Returns "" if nothing could be extracted.
    """
    mt = (mimetype or "").lower()
    p = path.lower()

    def _pdf():
        import pypdf
        reader = pypdf.PdfReader(path)
        return "\n".join((pg.extract_text() or "") for pg in reader.pages)

    def _docx():
        from docx import Document
        d = Document(path)
        parts = [para.text for para in d.paragraphs if para.text.strip()]
        for table in d.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)

    def _pptx():
        from pptx import Presentation
        prs = Presentation(path)
        parts = []
        for i, slide in enumerate(prs.slides, 1):
            slide_parts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    txt = shape.text_frame.text.strip()
                    if txt:
                        slide_parts.append(txt)
                if shape.has_table:
                    for row in shape.table.rows:
                        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if cells:
                            slide_parts.append(" | ".join(cells))
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                note = slide.notes_slide.notes_text_frame.text.strip()
                if note:
                    slide_parts.append(f"[Notas del orador: {note}]")
            if slide_parts:
                parts.append(f"[Diapositiva {i}]\n" + "\n".join(slide_parts))
        return "\n\n".join(parts)

    def _txt():
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # Choose parser order from the mimetype/extension hint; if unknown, try all.
    if "pdf" in mt or p.endswith(".pdf"):
        order = [_pdf]
    elif "wordprocessing" in mt or p.endswith(".docx"):
        order = [_docx]
    elif "presentation" in mt or p.endswith(".pptx"):
        order = [_pptx]
    elif "text" in mt or p.endswith((".txt", ".md", ".csv")):
        order = [_txt]
    else:
        order = [_pdf, _docx, _pptx, _txt]  # unknown/missing mimetype: best effort

    for fn in order:
        try:
            text = fn()
            if text and text.strip():
                return text.strip()
        except Exception as e:
            print(f"⚠️  {fn.__name__} extraction error: {e}")
            continue
    return ""


def _ensure_bf_updated_at_column(conn):
    """Add the bf_updated_at column to research_assets if it isn't there yet."""
    c = conn.cursor()
    try:
        cols = [row[1] for row in c.execute("PRAGMA table_info(research_assets)").fetchall()]
        if cols and "bf_updated_at" not in cols:
            c.execute("ALTER TABLE research_assets ADD COLUMN bf_updated_at TEXT")
            conn.commit()
    except Exception as e:
        print(f"⚠️  Could not ensure bf_updated_at column: {e}")


def _asset_indexed_ts(c, asset_id: str):
    """
    Returns False if the asset is NOT indexed yet; otherwise returns the stored
    Brandfolder updated_at timestamp (may be None for assets indexed before
    change-detection existed).
    """
    try:
        c.execute(
            "SELECT bf_updated_at FROM research_assets WHERE asset_id=? AND status='indexed' LIMIT 1",
            (asset_id,),
        )
    except sqlite3.OperationalError:
        c.execute(
            "SELECT NULL FROM research_assets WHERE asset_id=? AND status='indexed' LIMIT 1",
            (asset_id,),
        )
    row = c.fetchone()
    if row is None:
        return False
    return row[0]


def _asset_id_from_source(source: str) -> str:
    """Extract the Brandfolder asset id from a workbench source URL."""
    return (source or "").rstrip("/").split("/")[-1]


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
    _ensure_bf_updated_at_column(conn)

    # Create a log entry for this sync run
    c.execute(
        "INSERT INTO sync_log (status) VALUES ('running')"
    )
    conn.commit()
    log_id = c.lastrowid
    started_at = datetime.utcnow()

    stats = {"total_found": 0, "new_indexed": 0, "skipped": 0, "failed": 0, "reindexed": 0}

    try:
        from .brandfolder_service import BrandfolderAPI
        from .media_service import MediaService
        from .rag_service import RAGManager

        print("🔄 [AutoSync] Starting full library sync...")

        bf_api = BrandfolderAPI()
        rag = RAGManager()

        # 1. Get ALL Brandfolders (index the entire library, not just the first one)
        brandfolders = bf_api.get_brandfolders()
        if not brandfolders:
            raise ValueError("No Brandfolders accessible.")
        print(f"📚 [AutoSync] {len(brandfolders)} Brandfolder(s) accessible.")

        # 2. Get ALL assets from EVERY brandfolder (paginated, no search filter)
        raw_assets = []
        seen_asset_ids = set()
        for bf in brandfolders:
            bf_id = bf["id"]
            bf_name = bf.get("attributes", {}).get("name", bf_id)
            print(f"🔍 [AutoSync] Fetching assets from '{bf_name}' ({bf_id})...")
            bf_assets = bf_api.get_assets(brandfolder_id=bf_id, per_page=100)
            # Dedupe across brandfolders (an asset can appear via collections)
            unique = [a for a in bf_assets if a.get("id") and a["id"] not in seen_asset_ids]
            for a in unique:
                seen_asset_ids.add(a["id"])
            raw_assets.extend(unique)
            print(f"   → {len(bf_assets)} found in '{bf_name}' ({len(unique)} new across library)")

        stats["total_found"] = len(raw_assets)
        print(f"✅ [AutoSync] Found {len(raw_assets)} unique assets across all Brandfolders.")

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

            current_ts = info.get("updated_at")

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
                if "image" in mimetype:
                    asset_type = "image"
                    url = att.get("url")
                    break

            source_link = f"https://brandfolder.com/workbench/{asset_id}"

            # --- DEDUP + CHANGE DETECTION (fast SQLite check first) ---
            stored_ts = _asset_indexed_ts(c, asset_id)
            if stored_ts is not False:
                # Already indexed. Skip when unchanged OR when we have no stored
                # timestamp (legacy rows — do NOT re-process the whole library).
                if (not stored_ts) or (stored_ts == current_ts):
                    stats["skipped"] += 1
                    continue
                # Timestamp changed in Brandfolder → re-index this asset.
                print(f"🔁 [AutoSync] Re-indexing changed asset: {name}")
                rag.delete_document(source_link)
                c.execute("DELETE FROM research_assets WHERE asset_id=?", (asset_id,))
                conn.commit()
                stats["reindexed"] += 1
                # fall through to process
            elif rag.document_exists(source_link):
                # Present in the vector DB but not in local SQLite (e.g. after a
                # volume reset) — record it and skip re-embedding.
                print(f"⏭️  [AutoSync] Skipping (already in vector DB): {name}")
                c.execute(
                    "INSERT OR IGNORE INTO research_assets (session_id, asset_id, name, type, url, status, bf_updated_at) VALUES (?,?,?,?,?,?,?)",
                    (session_id, asset_id, name, asset_type, url, "indexed", current_ts)
                )
                conn.commit()
                stats["skipped"] += 1
                continue

            # --- PROCESS NEW (or changed) ASSET ---
            try:
                # Insert into DB with 'pending' status first
                c.execute(
                    "INSERT INTO research_assets (session_id, asset_id, name, type, url, status) VALUES (?,?,?,?,?,?)",
                    (session_id, asset_id, name, asset_type, url, "pending")
                )
                conn.commit()
                asset_row_id = c.lastrowid

                # Base content: name + type + the asset's Brandfolder description (HTML stripped)
                content = f"Asset: {name}\nType: {asset_type}"
                desc = _clean_html(info.get("description") or "")
                if desc:
                    content += f"\nDescripción: {desc}"

                if asset_type in ["video", "audio", "document", "image"]:
                    try:
                        fresh_details = bf_api.get_asset_details(asset_id)
                        fresh_info = bf_api.extract_asset_info(fresh_details)

                        # Add tags (only available from the detailed asset fetch)
                        if fresh_info.get("tags"):
                            content += "\nTags: " + ", ".join(fresh_info["tags"])
                        # If the description was empty in the list view, try the fresh one
                        if not desc:
                            fresh_desc = _clean_html(fresh_info.get("description") or "")
                            if fresh_desc:
                                content += f"\nDescripción: {fresh_desc}"

                        fresh_url = None
                        fresh_mime = ""
                        for att in fresh_info["attachments"]:
                            mimetype = att.get("mimetype") or ""
                            if asset_type == "video" and "video" in mimetype:
                                fresh_url = att.get("url"); fresh_mime = mimetype
                                break
                            if asset_type == "audio" and "audio" in mimetype:
                                fresh_url = att.get("url"); fresh_mime = mimetype
                                break
                            if asset_type == "image" and "image" in mimetype:
                                fresh_url = att.get("url"); fresh_mime = mimetype
                                break
                            if asset_type == "document" and any(x in mimetype for x in [
                                "pdf", "wordprocessing", "presentation", "officedocument",
                                "document", "msword", "ms-powerpoint", "text",
                            ]):
                                fresh_url = att.get("url"); fresh_mime = mimetype
                                break

                        # Fallback to first attachment for documents/images
                        if not fresh_url and asset_type in ("document", "image") and fresh_info["attachments"]:
                            fresh_url = fresh_info["attachments"][0].get("url")
                            fresh_mime = fresh_info["attachments"][0].get("mimetype") or ""

                        if fresh_url and fresh_url.startswith("http"):
                            local_path = bf_api.download_attachment(fresh_url)
                            if local_path:
                                if asset_type in ["video", "audio"]:
                                    mime = "video/mp4" if asset_type == "video" else "audio/mp3"
                                    transcript = media_service.transcribe_media(local_path, mime_type=mime)
                                    content += f"\n\n--- TRANSCRIPT ---\n{transcript}"
                                elif asset_type == "image":
                                    caption = media_service.describe_image(
                                        local_path, mime_type=(fresh_mime or "image/jpeg")
                                    )
                                    content += f"\n\n--- DESCRIPCIÓN DE LA IMAGEN (IA) ---\n{caption}"
                                elif asset_type == "document":
                                    doc_text = extract_text_from_document(local_path, fresh_mime)
                                    if doc_text.strip():
                                        content += f"\n\n--- DOCUMENT TEXT ---\n{doc_text}"
                                    else:
                                        print(f"⚠️  Sin texto extraíble de: {name} ({fresh_mime or 'mimetype desconocido'})")
                                os.remove(local_path)
                    except Exception as e:
                        print(f"⚠️  [AutoSync] Media processing failed for {name}: {e}")
                        content += f"\n\n[Extraction Failed: {e}]"

                # Index to Vector DB (store Brandfolder updated_at for change detection)
                rag.add_document(content, source_link, title=name, metadata={"bf_updated_at": current_ts})

                # Mark as indexed in DB
                c.execute(
                    "UPDATE research_assets SET status='indexed', content=?, bf_updated_at=? WHERE id=?",
                    (content, current_ts, asset_row_id)
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
            f"Re-indexed: {stats['reindexed']} | Skipped: {stats['skipped']} | "
            f"Failed: {stats['failed']}"
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


def coverage_stats() -> dict:
    """
    Report knowledge-base coverage: total documents vs. how many Brandfolder
    documents are indexed "name-only" (no extracted body). Read-only.
    """
    try:
        from .rag_service import RAGManager
        rag = RAGManager()
        total = rag.store.count_documents()
        analysis = rag.store.analyze_brandfolder_documents()
        mids = analysis["marker_ids"]
        thin = analysis["thin"]
        return {
            "total_documents": total,
            "brandfolder_documents": len(analysis["bf_docs"]),
            "thin_documents": len(thin),
            "rich_documents": max(total - len(thin), 0),
            "coverage_pct": round(100 * (total - len(thin)) / total, 1) if total else 0,
            "by_content": {
                "transcribed_media": len(mids.get("transcript", set())),
                "document_text": len(mids.get("document_text", set())),
                "image_described": len(mids.get("image", set())),
                "name_only": len(thin),
            },
        }
    except Exception as e:
        return {"error": str(e)}


def reindex_thin(limit: int = None, dry_run: bool = False) -> dict:
    """
    Retroactively fix documents indexed "name-only" (no extracted body): delete
    them and clear their local markers, then run full_sync() to re-ingest them
    with the multi-format extractor (Word/PowerPoint/PDF + description + tags).

    Args:
        limit: process at most this many thin documents (batching). None = all.
        dry_run: only count/report, delete nothing.
    """
    global _sync_running
    if _sync_running and not dry_run:
        return {"status": "busy", "message": "A sync is already running."}

    try:
        from .rag_service import RAGManager
        rag = RAGManager()
        thin = rag.find_thin_documents()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    total_thin = len(thin)
    if limit:
        thin = thin[:limit]

    if dry_run:
        return {
            "status": "dry_run",
            "thin_total": total_thin,
            "would_reindex": len(thin),
            "sample_sources": [t["source"] for t in thin[:20]],
        }

    if not thin:
        return {"status": "nothing_to_do", "thin_total": 0}

    # Delete the thin documents and clear their local 'indexed' markers so the
    # subsequent full_sync re-processes them from scratch.
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    _ensure_bf_updated_at_column(conn)
    cleared = 0
    for t in thin:
        try:
            rag.delete_document(t["source"])
            asset_id = _asset_id_from_source(t["source"])
            c.execute("DELETE FROM research_assets WHERE asset_id=?", (asset_id,))
            cleared += 1
        except Exception as e:
            print(f"⚠️  [Reindex] Could not clear {t['source']}: {e}")
    conn.commit()
    conn.close()

    print(f"🧹 [Reindex] Cleared {cleared} name-only documents. Running full_sync to re-ingest...")
    full_sync()

    return {
        "status": "completed",
        "thin_total": total_thin,
        "cleared_and_reingested": cleared,
        "note": "full_sync ran; re-check /sync/coverage for the new numbers.",
    }
