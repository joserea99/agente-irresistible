import sys
import os
from dotenv import load_dotenv

# Load env vars BEFORE imports to ensure API Keys are available
load_dotenv(".env")

try:
    from rag_manager import RAGManager
    print("✅ RAGManager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import RAGManager: {e}")
    # Attempt to fix path if backend is not found
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    try:
        from app.services.rag_service import RAGManager
        print("✅ RAGManager (Backend Service) imported successfully")
    except ImportError as e2:
        print(f"❌ Still failed: {e2}")
        sys.exit(1)

def test():
    print("🔄 Initializing RAGManager...")
    try:
        rag = RAGManager()
    except Exception as e:
        print(f"❌ Error initializing RAGManager: {e}")
        return

    print("\n📊 Checking Knowledge Base Stats...")
    try:
        count = rag.get_stats()
        print(f"📈 Document count in Cloud Brain: {count}")
    except Exception as e:
        print(f"❌ Error fetching stats: {e}")
        # Proceed to search anyway, stats might fail if permissions differ

    query = "que es el modelo de iglesia irresistible?"
    print(f"\n🔎 Searching for: '{query}'...")
    try:
        results = rag.search(query, n_results=2)
        
        if results:
            print("\n✅ Search Results found:")
            print("-" * 40)
            print(results[:600] + "...") # Print first 600 chars
            print("-" * 40)
        else:
            print("❌ No results found. Embeddings might not match or DB is empty.")
    except Exception as e:
        print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    test()
