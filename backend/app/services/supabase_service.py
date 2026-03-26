import os
import logging
from supabase import create_client, Client
from typing import Optional, Dict, List

from ..core.config import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    _instance = None
    client: Client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            if not settings.supabase_url or not settings.supabase_service_role_key:
                logger.warning("Supabase credentials missing. SupabaseService will fail.")
            else:
                cls._instance.client = create_client(settings.supabase_url, settings.supabase_service_role_key)
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
            logger.error(f"Error fetching profile {user_id}: {e}")
            return None

    def update_profile(self, user_id: str, data: Dict) -> bool:
        """Update user profile"""
        if not self.client: return False
        try:
            self.client.table("profiles").update(data).eq("id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating profile {user_id}: {e}")
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
            logger.error(f"Error creating session: {e}")
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
            logger.error(f"Error adding message: {e}")
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
            logger.error(f"Error fetching sessions: {e}")
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
            logger.error(f"Error fetching messages: {e}")
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
            logger.error(f"Error uploading file to {bucket}/{path}: {e}")
            return None

    def get_public_url(self, bucket: str, path: str) -> str:
        """Generates public URL for a file."""
        if not self.client: return ""
        try:
            return self.client.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            logger.error(f"Error getting public URL: {e}")
            return ""

    # --- Dojo Progress Methods ---

    def save_dojo_completion(self, user_id: str, scenario_id: str, scenario_name: str, score: int = 0) -> bool:
        """Save a completed dojo scenario for a user"""
        if not self.client: return False
        try:
            data = {
                "user_id": user_id,
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "score": score
            }
            self.client.table("dojo_completions").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving dojo completion: {e}")
            return False

    def get_dojo_progress(self, user_id: str) -> List[Dict]:
        """Get all completed dojo scenarios for a user"""
        if not self.client: return []
        try:
            response = self.client.table("dojo_completions") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("completed_at", desc=True) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching dojo progress: {e}")
            return []

# Singleton instance
supabase_service = SupabaseService()
