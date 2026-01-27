import chromadb
from chromadb.utils import embedding_functions
import os

# Persistent storage for the "Brain"
# In Railway with a Volume mounted at /app/brain_data
if os.path.exists("/app/brain_data"):
    CHROMA_PATH = "/app/brain_data/irresistible_brain_db"
else:
    # Local development
    # Ensure we point to the project root, not backend/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    CHROMA_PATH = os.path.join(project_root, "irresistible_brain_db")
    print(f"🧠 RAG DB Path: {CHROMA_PATH}")

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

    def document_exists(self, source_url):
        """Checks if a document with the given source_url already exists."""
        results = self.collection.get(
            where={"source": source_url},
            limit=1
        )
        return len(results["ids"]) > 0

    def add_document(self, content, source_url, title="Unknown"):
        """Ingests a document into the brain. Returns True if added, False if skipped (exists)."""
        # Check if already exists to prevent duplicates
        if self.document_exists(source_url):
            return False
            
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
        return True

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

    def get_recent_documents(self, limit=5):
        """Returns metadata of recent documents."""
        # Chroma doesn't strictly support "last inserted" without timestamp metadata
        # But grabbing a few is better than nothing for the dashboard
        try:
            # We get more than we need to try to filter unique titles
            results = self.collection.get(
                limit=limit * 2, 
                include=["metadatas"]
            )
            
            seen_titles = set()
            unique_docs = []
            
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    title = meta.get("title", "Unknown Asset")
                    if title not in seen_titles:
                        seen_titles.add(title)
                        unique_docs.append(meta)
                        if len(unique_docs) >= limit:
                            break
                            
            return unique_docs
        except Exception as e:
            print(f"Error fetching recent docs: {e}")
            return []

    def get_full_document(self, source_url):
        """Retrieves and stitches together all chunks for a given source."""
        try:
            results = self.collection.get(
                where={"source": source_url},
                include=["documents"]
            )
            
            if not results["documents"]:
                return None
                
            # Naive stitching: just join them. 
            # Since we chunked strictly by order of insertion (likely), 
            # we should technically sort by ID if IDs preserved order.
            # Our IDs are f"{source_url}_{i}", so we can sort by that.
            
            # Combine docs with ids to sort
            docs_with_ids = zip(results["ids"], results["documents"])
            sorted_docs = sorted(docs_with_ids, key=lambda x: int(x[0].split('_')[-1]))
            
            full_text = "".join([doc for _, doc in sorted_docs])
            return full_text
            
        except Exception as e:
            print(f"Error retrieving full doc: {e}")
            return None
