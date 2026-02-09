import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
# Load environment variables FIRST
load_dotenv("/Users/joserea/irresistible_agent/.env")

# If running on Railway, paths might be different. 
# We should allow CHROMA_PATH to be set via ENV or fallback to default
CHROMA_PATH = os.environ.get("CHROMA_PATH")
if not CHROMA_PATH:
    CHROMA_PATH = os.path.join(os.path.dirname(__file__), "irresistible_brain_db")


print(f"📂 Opening ChromaDB at: {CHROMA_PATH}")

def migrate():
    if not os.path.exists(CHROMA_PATH):
        print("❌ ChromaDB path not found!")
        return

    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection("irresistible_knowledge")
        print(f"✅ Connected to collection. Item count: {collection.count()}")
        
        # Fetch ALL data
        # Chroma .get() limits to 10 by default, set large limit
        all_data = collection.get(limit=10000, include=["documents", "metadatas"])
        
        documents = all_data["documents"]
        metadatas = all_data["metadatas"]
        
        if not documents:
            print("⚠️ No documents found in collection.")
            return

        print(f"🚀 Starting migration of {len(documents)} items...")
        
        success_count = 0
        skip_count = 0
        
        # Deduplication: Chroma store chunks, but we want to reconstruct Documents if possible
        # Or just store each chunk as a unique "document" source for now to ensure all text is preserved.
        # Given we are re-embedding, treating each Chroma Chunk as a Source Doc is safest to avoid data loss,
        # even if not perfectly semantic.
        # BUT, standard RAG chunks are small. Embeddings might be redundant.
        # Let's try to group by 'source' metadata if available.
        
        grouped_docs = {}
        
        for i, doc_text in enumerate(documents):
            meta = metadatas[i] if metadatas else {}
            source = meta.get("source", f"unknown_{i}")
            
            if source not in grouped_docs:
                grouped_docs[source] = []
            
            grouped_docs[source].append({
                "text": doc_text,
                "meta": meta
            })
            
        print(f"📦 Grouped into {len(grouped_docs)} unique source documents.")
        
        for source, chunks in grouped_docs.items():
            print(f"Processing {source}...")
            
            # Stitch content back together roughly
            # (Assuming chunk order is not guaranteed, we just concat. 
            # Ideally we'd sort by ID if IDs were structured like 'source_0', 'source_1')
            full_content = "\n\n".join([c["text"] for c in chunks])
            
            # Use metadata from first chunk
            first_meta = chunks[0]["meta"]
            title = first_meta.get("title", source)
            
            if vector_store.store_document(
                content=full_content,
                source=source,
                title=title,
                metadata=first_meta
            ):
                success_count += 1
            else:
                skip_count += 1
                
        print(f"🎉 Migration Complete!")
        print(f"✅ Successfully migrated: {success_count} documents")
        print(f"⏭️ Skipped (already existed): {skip_count} documents")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
