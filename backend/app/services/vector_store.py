import os
from google import genai
from .supabase_service import supabase_service
from typing import List, Dict, Optional
import uuid

# Configure Gemini
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

class VectorStoreService:
    def __init__(self):
        self.supabase = supabase_service.get_client()
        if GOOGLE_API_KEY:
            self.client = genai.Client(api_key=GOOGLE_API_KEY)
            self.embedding_model = "models/text-embedding-004" # Updated model
        else:
            self.client = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text using Gemini."""
        if not self.client:
            print("GOOGLE_API_KEY not found associated with embeddings")
            return []
        
        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Error embedding text: {e}")
            return []

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for query using Gemini."""
        if not self.client:
            return []
            
        try:
             # Queries often behave same as text for new models, or use task_type if supported
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Error embedding query: {e}")
            return []

    def store_document(self, content: str, source: str, title: str = None, metadata: Dict = None) -> bool:
        """
        Stores a document and its vectors in Supabase.
        1. Checks if document exists by source.
        2. If not, creates document record.
        3. Chunks content.
        4. Embeds chunks.
        5. Inserts into document_chunks.
        """
        if not self.supabase:
            print("Supabase client not initialized")
            return False

        # 1. Check if exists
        try:
            existing = self.supabase.table("documents").select("id").eq("source", source).execute()
            if existing.data and len(existing.data) > 0:
                print(f"Document {source} already exists. Skipping.")
                return False
        except Exception as e:
            print(f"Error checking document existence: {e}")
            return False

        # 2. Insert Document
        doc_id = str(uuid.uuid4())
        try:
            doc_data = {
                "id": doc_id,
                "source": source,
                "title": title or "Untitled",
                "doc_type": "text", # Default, can be refined
                "metadata": metadata or {}
            }
            self.supabase.table("documents").insert(doc_data).execute()
        except Exception as e:
            print(f"Error inserting document: {e}")
            return False

        # 3. Chunking (Simple for migration, enhance later)
        chunk_size = 1000
        overlap = 100
        chunks = []
        
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            chunks.append(chunk_text)
            start += (chunk_size - overlap)
        
        # 4. Process Chunks
        vectors_data = []
        for i, chunk_text in enumerate(chunks):
            embedding = self.embed_text(chunk_text)
            if embedding:
                vectors_data.append({
                    "document_id": doc_id,
                    "content": chunk_text,
                    "embedding": embedding,
                    "chunk_index": i,
                    "metadata": metadata or {}
                })
        
        # 5. Insert Vectors (Batch if possible, but 1 by 1 is safer for loops)
        if vectors_data:
            try:
                self.supabase.table("document_chunks").insert(vectors_data).execute()
                print(f"✅ Stored {len(vectors_data)} chunks for {source}")
                return True
            except Exception as e:
                print(f"Error inserting chunks for {source}: {e}")
                # Clean up document if chunks failed? ideally yes.
                return False
        
        return True

    def search_similar(self, query: str, limit: int = 5) -> str:
        """
        Searches for context relevant to the query.
        Returns formatted context string.
        """
        if not self.supabase: return ""
        
        query_vector = self.embed_query(query)
        if not query_vector: return ""
        
        try:
            response = self.supabase.rpc("match_documents", {
                "query_embedding": query_vector,
                "match_threshold": 0.5, # Tune this
                "match_count": limit
            }).execute()
            
            if response.data:
                context = []
                for item in response.data:
                    context.append(f"[Source: Unknown ID {item['document_id']}]\n{item['content']}")
                return "\n\n".join(context)
                
        except Exception as e:
            print(f"Error searching vectors: {e}")
            
        return ""

vector_store = VectorStoreService()
