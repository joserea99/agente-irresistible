from typing import List, Dict, Optional
from .supabase_service import supabase_service

class ChatHistoryService:
    def __init__(self):
        # Supabase is initialized in its own service
        pass

    def create_session(self, user_id: str, director: str, title: str = "Nueva Conversación") -> Optional[str]:
        """Creates a new chat session and returns its ID."""
        return supabase_service.create_chat_session(user_id, director, title)

    def add_message(self, session_id: str, role: str, content: str):
        """Adds a message to a session."""
        supabase_service.add_message(session_id, role, content)

    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Returns all sessions for a user, ordered by most recent update."""
        return supabase_service.get_user_sessions(user_id)

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Returns full message history for a session."""
        return supabase_service.get_session_messages(session_id)

    def update_session_title(self, session_id: str, title: str):
        """Updates the title of a session."""
        if supabase_service.client:
            try:
                supabase_service.client.table("chat_sessions").update({"title": title}).eq("id", session_id).execute()
            except Exception as e:
                print(f"Error updating title: {e}")

    def delete_session(self, session_id: str):
        """Deletes a session and its messages."""
        if supabase_service.client:
            try:
                # Messages cascade delete automatically due to foreign key constraint
                supabase_service.client.table("chat_sessions").delete().eq("id", session_id).execute()
            except Exception as e:
                print(f"Error deleting session: {e}")
