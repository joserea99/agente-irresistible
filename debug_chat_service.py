import os
import sys

# Add backend to path (insert at 0 to prioritize over root app.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.chat_service import ChatService
from dotenv import load_dotenv

load_dotenv()

def test_chat():
    print("🧪 Testing ChatService...")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not set. Cannot test authentic API call.")
        return

    try:
        service = ChatService(api_key=api_key)
        print("✅ Service initialized.")
        
        print("📤 Sending test message...")
        response = service.generate_response(
            user_input="Hello, how are you?",
            history=[],
            director="Programación de Servicio"
        )
        print(f"📥 Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat()
