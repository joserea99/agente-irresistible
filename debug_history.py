import os
import sys

# Add backend to path (insert at 0 to prioritize over root app.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.chat_history_service import ChatHistoryService

def test_history():
    print("🧪 Testing ChatHistoryService...")
    
    try:
        service = ChatHistoryService()
        print(f"✅ Service initialized.")
        
        user_id = "test_user_debug"
        director = "Programación de Servicio"
        title = "Debug Session"
        
        print("📝 Creating session...")
        session_id = service.create_session(user_id, director, title)
        print(f"✅ Session created: {session_id}")
        
        print("📝 Adding message...")
        service.add_message(session_id, "user", "Hello Debug")
        print("✅ Message added.")
        
        print("📖 Reading messages...")
        msgs = service.get_session_messages(session_id)
        print(f"✅ Messages retrieved: {len(msgs)}")
        print(msgs)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_history()
