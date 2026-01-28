
import sqlite3
import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional

# DB Path (Same volume as auth/research DB)
if os.path.exists("/app/brain_data"):
    DB_PATH = "/app/brain_data/irresistible_app.db"
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.abspath(os.path.join(current_dir, "../../..", "irresistible_app.db"))

class ChatHistoryService:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Chat Sessions Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                director TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chat Messages Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                role TEXT, -- user, assistant
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_session(self, user_id: str, director: str, title: str = "New Conversation") -> str:
        """Creates a new chat session and returns its ID."""
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO chat_sessions (id, user_id, title, director) VALUES (?, ?, ?, ?)",
            (session_id, user_id, title, director)
        )
        conn.commit()
        conn.close()
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """Adds a message to a session."""
        message_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO chat_messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (message_id, session_id, role, content)
        )
        # Update session timestamp
        c.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        return message_id

    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Returns all sessions for a user, ordered by most recent update."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC", 
            (user_id,)
        )
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Returns full message history for a session."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC", 
            (session_id,)
        )
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_session_title(self, session_id: str, title: str):
        """Updates the title of a session."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (title, session_id))
        conn.commit()
        conn.close()

    def delete_session(self, session_id: str):
        """Deletes a session and its messages."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        c.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
