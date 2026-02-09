import sys
import os

# Ensure backend/app/services is in path if needed, or import relatively
# Assuming raw import from backend.app.services works if running from root
from backend.app.services.vector_store import vector_store

class RAGManager:
    def __init__(self):
        self.store = vector_store

    def document_exists(self, source_url):
        # Retrieve from Supabase to check existence
        # Check 'documents' table
        try:
            res = self.store.supabase.table("documents").select("id").eq("source", source_url).execute()
            return len(res.data) > 0
        except:
            return False

    def add_document(self, content, source_url, title="Unknown"):
        # Wrapper for store_document
        return self.store.store_document(content, source_url, title)

    def search(self, query, n_results=3):
        # Wrapper for search_similar
        return self.store.search_similar(query, limit=n_results)

    def get_stats(self):
        # Count documents
        try:
            res = self.store.supabase.table("documents").select("*", count="exact", head=True).execute()
            return res.count
        except:
            return 0
