
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.path.abspath("/Users/joserea/irresistible_agent/backend"))

from app.services.rag_service import RAGManager
from app.services.magic_service import MagicService

async def debug():
    print("🔍 Starting Debug Magic Actions...")
    
    # 1. Check Env Vars
    api_key = os.environ.get("GOOGLE_API_KEY")
    print(f"🔑 GOOGLE_API_KEY present: {bool(api_key)}")
    if api_key:
        print(f"🔑 Key starts with: {api_key[:5]}...")
    
    # 2. Check RAG Stats and Recent Docs
    rag = RAGManager()
    stats = rag.get_stats()
    print(f"📊 Document Count: {stats}")
    
    recent_docs = rag.get_recent_documents(limit=5)
    print(f"📄 Recent Documents ({len(recent_docs)}):")
    
    test_doc = None
    for doc in recent_docs:
        print(f"  - ID: {doc.get('id')}")
        print(f"    Title: {doc.get('title')}")
        print(f"    Source: {doc.get('source')}")
        test_doc = doc
        
    if not test_doc:
        print("❌ No documents found to test.")
        return

    # 3. Test Get Full Content
    print(f"\n🧪 Testing Content Retrieval for: {test_doc.get('title')}")
    source = test_doc.get('source')
    content = rag.get_full_document(source)
    
    if content:
        print(f"✅ Content Retrieved! Length: {len(content)} chars")
        print(f"Snippet: {content[:100]}...")
    else:
        print(f"❌ Content Retrieval FAILED for source: {source}")
        # Try to find why
        # Check if chunks exist manually?
        # Maybe use vector_store directly
        pass

    # 4. Test Magic Service (Gemini)
    print(f"\n✨ Testing Magic Service (Gemini)...")
    magic = MagicService()
    
    if not content:
        print("⚠️ Using dummy content for Gemini test since retrieval failed.")
        content = "Leadership is about serving others and creating a vision for the future."
        
    try:
        # Simple test
        prompt = "Say 'Hello World' in Spanish."
        res = magic._call_llm(prompt)
        print(f"🤖 Gemini Response: {res}")
        
        if "Error" in res:
             print("❌ Gemini Service Reported Error.")
        else:
             print("✅ Gemini Service Functional.")
             
    except Exception as e:
        print(f"❌ Gemini Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug())
