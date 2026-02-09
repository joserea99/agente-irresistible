from .vector_store import vector_store
import os

class RAGManager:
    def __init__(self):
        self.store = vector_store
        self.supabase = self.store.supabase

    def document_exists(self, source_url):
        """Checks if a document with the given source_url already exists."""
        try:
            res = self.supabase.table("documents").select("id").eq("source", source_url).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"Error checking doc existence: {e}")
            return False

    def add_document(self, content, source_url, title="Unknown"):
        """Ingests a document into the brain."""
        return self.store.store_document(content, source_url, title)

    def search(self, query, n_results=3):
        """Retrieves relevant context for a query."""
        return self.store.search_similar(query, limit=n_results)

    def get_stats(self):
        """Returns the number of documents in memory."""
        try:
            res = self.supabase.table("documents").select("*", count="exact", head=True).execute()
            return res.count
        except:
            return 0

    def get_recent_documents(self, limit=5):
        """Returns metadata of recent documents."""
        try:
            res = self.supabase.table("documents").select("*").order("created_at", desc=True).limit(limit).execute()
            return res.data
        except Exception as e:
            print(f"Error fetching recent docs: {e}")
            return []

    def get_full_document(self, source_url):
        """Retrieves and stitches together all chunks for a given source."""
        try:
            # 1. Get Document ID
            doc_res = self.supabase.table("documents").select("id").eq("source", source_url).single().execute()
            if not doc_res.data:
                return None
            
            doc_id = doc_res.data["id"]
            
            # 2. Get Chunks sorted by index
            chunks_res = self.supabase.table("document_chunks")\
                .select("content")\
                .eq("document_id", doc_id)\
                .order("chunk_index")\
                .execute()
                
            if not chunks_res.data:
                return None
                
            # 3. Join
            full_text = "".join([c["content"] for c in chunks_res.data])
            return full_text
            
        except Exception as e:
            print(f"Error retrieving full doc: {e}")
            return None
