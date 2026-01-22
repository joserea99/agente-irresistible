import sqlite3
import hashlib
import os
from datetime import datetime

# Use SQLite for local development, easy to switch to Postgres later
# In Railway with a Volume mounted at /app/brain_data
if os.path.exists("/app/brain_data"):
    DB_PATH = "/app/brain_data/irresistible_app.db"
else:
    DB_PATH = "irresistible_app.db"

def init_db():
    """Initializes the database with users and chat_history tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Chat History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(username, password, full_name, role="member"):
    """Adds a new user to the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Simple hashing (in production use bcrypt/Argon2)
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                  (username, pwd_hash, full_name, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """Verifies user credentials."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT full_name, role FROM users WHERE username=? AND password_hash=?", (username, pwd_hash))
    user = c.fetchone()
    
    conn.close()
    return user # Returns (full_name, role) or None

def save_message(username, role, content):
    """Saves a chat message."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (username, role, content) VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

def get_chat_history(username, limit=50):
    """Retrieves chat history for a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM chat_history WHERE username=? ORDER BY timestamp ASC LIMIT ?", (username, limit))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

# Initialize DB on first import
if not os.path.exists(DB_PATH):
    init_db()
