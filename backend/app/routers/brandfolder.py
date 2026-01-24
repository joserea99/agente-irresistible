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
    from ..services.research_service import ResearchService
    service = ResearchService()
    return service.create_session(request.username, request.query)

@router.get("/research/history")
async def get_research_history(username: str):
    from ..services.research_service import ResearchService
    service = ResearchService()
    return service.get_history(username)

@router.get("/research/{session_id}")
async def get_research_session(session_id: str):
    from ..services.research_service import ResearchService
    service = ResearchService()
    return service.get_session_status(session_id)

@router.post("/research/{session_id}/execute")
async def execute_research(session_id: str, background_tasks: fastapi.BackgroundTasks):
    from ..services.research_service import ResearchService
    service = ResearchService()
    
    # Run in background to avoid timeout
    background_tasks.add_task(service.execute_session, session_id)
    
    return {"message": "Deep Research started in background. Check status for updates."}

