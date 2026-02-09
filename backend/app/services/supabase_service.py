import os
from supabase import create_client, Client
from typing import Optional, Dict, List

# Load env inside the service to ensure they are loaded
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

class SupabaseService:
    _instance = None
    client: Client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("⚠️ Supabase credentials missing. SupabaseService will fail.")
            else:
                cls._instance.client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return cls._instance

    def get_client(self) -> Client:
        return self.client

    # --- Profile / User Methods ---

    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Fetch user profile by ID (from public.profiles)"""
        if not self.client: return None
        try:
            response = self.client.table("profiles").select("*").eq("id", user_id).single().execute()
            return response.data
        except Exception as e:
            print(f"Error fetching profile {user_id}: {e}")
            return None

    def update_profile(self, user_id: str, data: Dict) -> bool:
        """Update user profile"""
        if not self.client: return False
        try:
            self.client.table("profiles").update(data).eq("id", user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating profile {user_id}: {e}")
            return False

    # --- Chat History Methods ---

    def create_chat_session(self, user_id: str, director: str, title: str = "Nueva Conversación") -> Optional[str]:
        """Create a new chat session"""
        if not self.client: return None
        try:
            data = {
                "user_id": user_id,
                "director": director,
                "title": title
            }
            response = self.client.table("chat_sessions").insert(data).execute()
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to a session"""
        if not self.client: return False
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content
            }
            self.client.table("chat_messages").insert(data).execute()
            
            # Update session timestamp
            self.client.table("chat_sessions").update({
                "updated_at": "now()"
            }).eq("id", session_id).execute()
            
            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False

    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all sessions for a user"""
        if not self.client: return []
        try:
            response = self.client.table("chat_sessions") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("updated_at", desc=True) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get all messages for a session"""
        if not self.client: return []
        try:
            response = self.client.table("chat_messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .order("created_at", desc=False) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    # --- Storage Methods ---

    def upload_file(self, bucket: str, path: str, file_bytes: bytes, content_type: str = "text/plain") -> Optional[str]:
        """Uploads a file to Supabase Storage and returns its public URL."""
        if not self.client: return None
        try:
            self.client.storage.from_(bucket).upload(
                path=path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            return self.get_public_url(bucket, path)
        except Exception as e:
            print(f"Error uploading file to {bucket}/{path}: {e}")
            return None

    def get_public_url(self, bucket: str, path: str) -> str:
        """Generates public URL for a file."""
        if not self.client: return ""
        try:
            return self.client.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            print(f"Error getting public URL: {e}")
            return ""

# Singleton instance
supabase_service = SupabaseService()
