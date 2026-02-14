import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def verify_tables():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials in .env")
        return

    try:
        supabase = create_client(url, key)
        print("✅ Client connected.")
        
        # Check chat_sessions
        print("🔍 Checking 'chat_sessions' table...")
        try:
            supabase.table("chat_sessions").select("id").limit(1).execute()
            print("✅ 'chat_sessions' exists.")
        except Exception as e:
            print(f"❌ Error accessing 'chat_sessions': {e}")

        # Check chat_messages
        print("🔍 Checking 'chat_messages' table...")
        try:
            supabase.table("chat_messages").select("id").limit(1).execute()
            print("✅ 'chat_messages' exists.")
        except Exception as e:
            print(f"❌ Error accessing 'chat_messages': {e}")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_tables()
