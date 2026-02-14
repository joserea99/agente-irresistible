import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from app.services.rag_service import RAGManager

def check_stats():
    print("Checking Knowledge Base Stats...")
    try:
        rag = RAGManager()
        
        # Check connection
        print(f"Supabase Client: {rag.supabase}")
        
        # Get count
        print("Fetching count...")
        res = rag.supabase.table("documents").select("*", count="exact", head=True).execute()
        print(f"Count Result: {res}")
        print(f"Count Value: {res.count}")
        
        # Get recent
        print("Fetching recent...")
        recent = rag.get_recent_documents(limit=5)
        print(f"Recent Docs: {len(recent)}")
        for doc in recent:
            print(f" - {doc.get('title', 'No Title')} ({doc.get('source')})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_stats()
