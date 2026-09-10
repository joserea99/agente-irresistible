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

    @staticmethod
    def _chunk_text(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks on natural boundaries (paragraphs,
        then sentences) so chunks don't cut sentences mid-word. Falls back to
        a hard character split only for oversized paragraphs.
        """
        import re

        content = (content or "").strip()
        if not content:
            return []

        # Break into paragraphs first, then sentences for oversized ones.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
        units: List[str] = []
        for para in paragraphs:
            if len(para) <= chunk_size:
                units.append(para)
            else:
                # Split big paragraphs by sentence boundaries
                sentences = re.split(r"(?<=[.!?])\s+", para)
                buf = ""
                for s in sentences:
                    if len(buf) + len(s) + 1 <= chunk_size:
                        buf = f"{buf} {s}".strip()
                    else:
                        if buf:
                            units.append(buf)
                        # A single sentence longer than chunk_size: hard split
                        while len(s) > chunk_size:
                            units.append(s[:chunk_size])
                            s = s[chunk_size:]
                        buf = s
                if buf:
                    units.append(buf)

        # Greedily pack units into chunks with overlap carried between them.
        chunks: List[str] = []
        current = ""
        for unit in units:
            if len(current) + len(unit) + 2 <= chunk_size:
                current = f"{current}\n\n{unit}".strip()
            else:
                if current:
                    chunks.append(current)
                    # Carry the tail of the previous chunk as overlap for continuity
                    tail = current[-overlap:] if overlap else ""
                    current = f"{tail}\n\n{unit}".strip() if tail else unit
                else:
                    current = unit
        if current:
            chunks.append(current)

        return chunks

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

        # 3. Chunking (paragraph-aware: avoid cutting sentences mid-word)
        chunks = self._chunk_text(content, chunk_size=1000, overlap=100)

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

    def get_document_meta(self, source: str) -> Optional[Dict]:
        """Return the stored document row (id, metadata) for a source, or None."""
        if not self.supabase:
            return None
        try:
            res = self.supabase.table("documents").select("id, metadata").eq("source", source).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching document meta for {source}: {e}")
            return None

    def delete_document(self, source: str) -> bool:
        """Delete a document and all of its chunks, addressed by source URL."""
        if not self.supabase:
            return False
        try:
            res = self.supabase.table("documents").select("id").eq("source", source).execute()
            if not res.data:
                return False
            for row in res.data:
                doc_id = row["id"]
                self.supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
                self.supabase.table("documents").delete().eq("id", doc_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting document {source}: {e}")
            return False

    def find_thin_document_ids(self) -> List[Dict]:
        """
        Find Brandfolder documents indexed WITHOUT an extracted body ("name-only"):
        none of their chunks contain a rich-content marker. Efficient — the marker
        queries return only ids, then we diff against all Brandfolder documents.
        Returns a list of {"id", "source"}.
        """
        if not self.supabase:
            return []

        rich_ids = set()
        markers = ["--- DOCUMENT TEXT ---", "--- TRANSCRIPT ---", "DESCRIPCIÓN DE LA IMAGEN"]
        for marker in markers:
            start = 0
            page = 1000
            while True:
                try:
                    res = self.supabase.table("document_chunks").select("document_id")\
                        .ilike("content", f"%{marker}%").range(start, start + page - 1).execute()
                except Exception as e:
                    logger.error(f"thin-scan marker query failed ({marker}): {e}")
                    break
                rows = res.data or []
                for r in rows:
                    rich_ids.add(r["document_id"])
                if len(rows) < page:
                    break
                start += page

        thin = []
        start = 0
        page = 1000
        while True:
            try:
                res = self.supabase.table("documents").select("id, source")\
                    .ilike("source", "%brandfolder.com/workbench/%").range(start, start + page - 1).execute()
            except Exception as e:
                logger.error(f"thin-scan documents query failed: {e}")
                break
            rows = res.data or []
            for r in rows:
                if r["id"] not in rich_ids:
                    thin.append({"id": r["id"], "source": r["source"]})
            if len(rows) < page:
                break
            start += page

        return thin

    def count_documents(self) -> int:
        if not self.supabase:
            return 0
        try:
            res = self.supabase.table("documents").select("id", count="exact", head=True).execute()
            return res.count or 0
        except Exception:
            return 0

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
