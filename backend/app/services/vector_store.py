import os
import logging
from google import genai
from .supabase_service import supabase_service
from typing import List, Dict, Optional
import uuid

from ..core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.supabase = supabase_service.get_client()
        if settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
            self.embedding_model = settings.gemini_embedding_model
        else:
            self.client = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text using Gemini."""
        if not self.client:
            logger.warning("GOOGLE_API_KEY not found for embeddings")
            return []

        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            if not response or not response.embeddings:
                logger.warning("No embeddings returned for text")
                return []
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return []

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for query using Gemini."""
        if not self.client:
            return []

        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            if not response or not response.embeddings:
                 return []
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return []

    def store_document(self, content: str, source: str, title: str = None, metadata: Dict = None) -> bool:
        """
        Stores a document and its vectors in Supabase.
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return False

        # 1. Check if exists
        try:
            existing = self.supabase.table("documents").select("id").eq("source", source).execute()
            if existing.data and len(existing.data) > 0:
                logger.info(f"Document {source} already exists. Skipping.")
                return False
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False

        # 2. Insert Document
        doc_id = str(uuid.uuid4())
        try:
            doc_data = {
                "id": doc_id,
                "source": source,
                "title": title or "Untitled",
                "doc_type": "text",
                "metadata": metadata or {}
            }
            self.supabase.table("documents").insert(doc_data).execute()
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            return False

        # 3. Chunking
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

        # 5. Insert Vectors
        if vectors_data:
            try:
                self.supabase.table("document_chunks").insert(vectors_data).execute()
                logger.info(f"Stored {len(vectors_data)} chunks for {source}")
                return True
            except Exception as e:
                logger.error(f"Error inserting chunks for {source}: {e}")
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
                "match_threshold": 0.5,
                "match_count": limit
            }).execute()

            if response.data:
                context = []
                for item in response.data:
                    context.append(f"[Source: {item['document_id']}]\n{item['content']}")
                return "\n\n".join(context)

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")

        return ""

vector_store = VectorStoreService()
