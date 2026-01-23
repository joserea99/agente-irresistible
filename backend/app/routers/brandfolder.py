from fastapi import APIRouter, HTTPException, Depends
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
            
        count = 0
        skipped = 0
        
        for asset in assets:
            info = api.extract_asset_info(asset)
            
            # Simple indexing of description and name
            # In real app, download attachment, extract text, transcribe, etc.
            content = f"Asset: {info['name']}\nDescription: {info['description']}\nTags: {', '.join(info['tags'])}"
            
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
