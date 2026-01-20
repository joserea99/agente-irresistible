import chromadb
from chromadb.utils import embedding_functions
import os

# Persistent storage for the "Brain"
CHROMA_PATH = "irresistible_brain_db"

class RAGManager:
    def __init__(self):
        # Initialize Chroma Client with persistence
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        # Use default embedding function (can be swapped for OpenAI)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name="irresistible_knowledge",
            embedding_function=self.embedding_fn
        )

    def add_document(self, content, source_url, title="Unknown"):
        """Ingests a document into the brain."""
        # Simple chunking (in production use LangChain RecursiveCharacterTextSplitter)
        # For now, we store the whole chunk if it's small, or split blindly
        
        chunk_size = 1000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        ids = [f"{source_url}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_url, "title": title} for _ in chunks]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return len(chunks)

    def search(self, query, n_results=3):
        """Retrieves relevant context for a query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results nicely
        context = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                context.append(f"[Source: {meta['source']}]\n{doc}")
        
        return "\n\n".join(context)

    def get_stats(self):
        """Returns the number of documents in memory."""
        return self.collection.count()
