from fastapi import APIRouter, HTTPException, Depends
import fastapi
from ..models.brandfolder import SearchRequest, IngestRequest
from ..services.brandfolder_service import BrandfolderAPI
from ..services.rag_service import RAGManager
from ..services.chat_service import ChatService

router = APIRouter()

@router.post("/search")
async def search_assets(request: SearchRequest):
    try:
        api = BrandfolderAPI()
        # Use first brandfolder if not specified
        bf_id = request.brandfolder_id
        if not bf_id:
             bfs = api.get_brandfolders()
             if bfs:
                 bf_id = bfs[0]["id"]
             else:
                 raise HTTPException(status_code=404, detail="No brandfolders found")
                 
        results = api.search_assets(bf_id, request.query)
        
        # Simplify results for frontend
        simple_results = []
        for asset in results:
            info = api.extract_asset_info(asset)
            simple_results.append(info)
            
        return {"results": simple_results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_assets(request: IngestRequest):
    try:
        api = BrandfolderAPI()
        rag = RAGManager()
        
        bf_id = request.brandfolder_id
        if not bf_id:
             bfs = api.get_brandfolders()
             if bfs:
                 bf_id = bfs[0]["id"]
        
        # Get assets
        if request.topic:
            # Optimize query using LLM (Spanish -> English + Synonyms)
            chat = ChatService()
            optimized_topic = chat.optimize_query(request.topic)
            print(f"🧠 Optimized ingestion topic: {request.topic} -> {optimized_topic}")
            
            assets = api.search_assets(bf_id, optimized_topic)
        else:
            assets = api.get_assets(brandfolder_id=bf_id, per_page=request.max_assets)
            
        # Initialize Media Service
        from ..services.media_service import MediaService
        media_service = MediaService()

        count = 0
        skipped = 0
        
        for asset in assets:
            info = api.extract_asset_info(asset)
            
            content = f"Asset: {info['name']}\nDescription: {info['description']}\nTags: {', '.join(info['tags'])}"
            
            # Check for Media Attachments (Video/Audio)
            # We look for the first valid media attachment to transcribe
            transcript = ""
            for att in info['attachments']:
                mime = att.get('mimetype', '')
                url = att.get('url')
                
                if url and ('video' in mime or 'audio' in mime):
                    print(f"🎙️ Found media asset: {info['name']} ({mime})")
                    try:
                        # Download temporarily
                        temp_file = api.download_attachment(url)
                        if temp_file:
                            # Transcribe
                            transcript = media_service.transcribe_media(temp_file, mime_type=mime)
                            
                            # Append to content
                            content += f"\n\n--- TRANSCRIPTION ---\n{transcript}\n---------------------"
                            
                            # Clean up
                            import os
                            os.remove(temp_file)
                            break # Only transcribe the first main media file per asset
                    except Exception as e:
                        print(f"⚠️ Failed to process media for {info['name']}: {e}")

            # Use 'web_view_link' or attachment url as source
            source = f"https://brandfolder.com/workbench/{info['id']}" 
            
            if rag.add_document(content, source, title=info['name']):
                count += 1
            else:
                skipped += 1
                
        return {"indexed": count, "skipped": skipped, "message": f"Processed {len(assets)} assets"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """Returns statistics about the knowledge base."""
    try:
        rag = RAGManager()
        count = rag.get_stats()
        recent = rag.get_recent_documents(limit=5)
        return {
            "document_count": count,
            "recent_documents": recent
        }
    except Exception as e:
        # If DB isn't initialized or other error, return 0
        print(f"Stats error: {e}")
        return {"document_count": 0, "recent_documents": []}


# --------------------------
# DEEP RESEARCH ENDPOINTS
# --------------------------
from pydantic import BaseModel

class ResearchStartRequest(BaseModel):
    query: str
    username: str

@router.post("/research/start")
async def start_research(request: ResearchStartRequest):
    try:
        from ..services.research_service import ResearchService
        service = ResearchService()
        return service.create_session(request.username, request.query)
    except Exception as e:
        print(f"❌ Research Start Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/history")
async def get_research_history(username: str):
    try:
        from ..services.research_service import ResearchService
        service = ResearchService()
        return service.get_history(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/{session_id}")
async def get_research_session(session_id: str):
    try:
        from ..services.research_service import ResearchService
        service = ResearchService()
        session = service.get_session_status(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Session Status Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research/{session_id}/execute")
async def execute_research(session_id: str, background_tasks: fastapi.BackgroundTasks):
    try:
        from ..services.research_service import ResearchService
        service = ResearchService()
        
        # Run in background to avoid timeout
        background_tasks.add_task(service.execute_session, session_id)
        
        return {"message": "Deep Research started in background. Check status for updates."}


@router.get("/research/debug/diagnose")
async def debug_research_config():
    """Diagnostic endpoint to check why Research might be failing."""
    import os
    import sqlite3
    
    report = {
        "env_vars": {
            "BRANDFOLDER_API_KEY_EXISTS": bool(os.environ.get("BRANDFOLDER_API_KEY")),
            "GOOGLE_API_KEY_EXISTS": bool(os.environ.get("GOOGLE_API_KEY")),
            "RAILWAY_ENVIRONMENT": os.environ.get("RAILWAY_ENVIRONMENT_NAME", "local")
        },
        "volume": {
            "exists": os.path.exists("/app/brain_data"),
            "writable": os.access("/app/brain_data", os.W_OK) if os.path.exists("/app/brain_data") else "N/A"
        },
        "db": {
            "path": "/app/brain_data/irresistible_app.db" if os.path.exists("/app/brain_data") else "local",
            "connection": "pending"
        },
        "services": {}
    }
    
    # Test DB
    try:
        db_path = report["db"]["path"]
        if db_path == "local":
             current_dir = os.path.dirname(os.path.abspath(__file__))
             db_path = os.path.abspath(os.path.join(current_dir, "../../..", "irresistible_app.db"))
             
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT 1")
        conn.close()
        report["db"]["connection"] = "ok"
    except Exception as e:
        report["db"]["connection"] = f"failed: {str(e)}"
        
    # Test Services Init
    try:
        from ..services.brandfolder_service import BrandfolderAPI
        api = BrandfolderAPI()
        bfs = api.get_brandfolders()
        report["services"]["brandfolder"] = f"ok (found {len(bfs)})"
    except Exception as e:
        report["services"]["brandfolder"] = f"failed: {str(e)}"
        
    try:
        from ..services.chat_service import ChatService
        chat = ChatService()
        report["services"]["chat"] = "ok" if chat.llm else "ok (no key)"
    except Exception as e:
        report["services"]["chat"] = f"failed: {str(e)}"
        
    return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

