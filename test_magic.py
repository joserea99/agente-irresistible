import requests
import json
from backend.app.services.rag_service import RAGManager

def test_magic_generation():
    # 1. Setup Data in RAG
    rag = RAGManager()
    dummy_text = """
    The best leaders are not those who command, but those who serve. 
    Servant leadership is about putting the needs of others first. 
    When you help others grow, the organization grows. EXPERIMENT: Try saying 'How can I help?' in every meeting this week.
    """
    dummy_source = "http://test-source.com/leadership-article"
    
    print("🧠 Adding dummy doc to RAG...")
    added = rag.add_document(dummy_text, dummy_source, title="Servant Leadership 101")
    print(f"   -> Added? {added}")
    
    # Verify locally
    local_doc = rag.get_full_document(dummy_source)
    print(f"   -> Local Retrieval: {'Found' if local_doc else 'None'} ({len(local_doc) if local_doc else 0} chars)")

    # 2. Call API
    url = "http://localhost:8000/magic/generate"
    payload = {
        "document_source": dummy_source,
        "action_type": "social"
    }
    
    print(f"🪄 Calling Magic API for source: {dummy_source}")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Magic API Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_magic_generation()
