import sqlite3
import hashlib
import os
import json
from datetime import datetime, timedelta

# Use SQLite for local development, easy to switch to Postgres later
# In Railway with a Volume mounted at /app/brain_data
# Use absolute path for DB to avoid working directory issues
current_dir = os.path.dirname(os.path.abspath(__file__))
# The DB is in the root of the project (two levels up from services/auth_service.py)
DB_PATH = os.path.abspath(os.path.join(current_dir, "../../..", "irresistible_app.db"))


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
            trial_start_date TIMESTAMP,
            subscription_status TEXT DEFAULT 'trial',
            known_devices TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if new columns exist (simple migration for existing DB)
    try:
        c.execute("ALTER TABLE users ADD COLUMN trial_start_date TIMESTAMP")
        c.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'trial'")
        c.execute("ALTER TABLE users ADD COLUMN known_devices TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass # Columns likely exist
    
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
    
    trial_start = datetime.utcnow()
    devices = json.dumps([role]) # temporary abuse of role arg, actually we need to pass device_fingerprint from args
    # But for cleaner API, let's fix the verify_user flow instead
    
    try:
        # Default to empty devices list here, update on login
        c.execute("INSERT INTO users (username, password_hash, full_name, role, trial_start_date, subscription_status, known_devices) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (username, pwd_hash, full_name, role, trial_start, 'trial', '[]'))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password, device_fingerprint="unknown"):
    """Verifies user credentials and checks SaaS Constraints."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pwd_hash))
    user = c.fetchone()
    
    conn.close()
    
    if not user:
        return None, "invalid_credentials"
        
    # 1. Check Trial / Subscription
    trial_start = datetime.strptime(user['trial_start_date'], '%Y-%m-%d %H:%M:%S.%f') if user['trial_start_date'] else datetime.utcnow()
    status = user['subscription_status']
    
    if status == 'trial':
        days_left = 14 - (datetime.utcnow() - trial_start).days
        if days_left < 0:
            return None, "trial_expired"
            
    if status == 'expired':
        return None, "subscription_expired"

    # 2. Check Device
    known_devices = json.loads(user['known_devices'])
    if device_fingerprint not in known_devices and device_fingerprint != "unknown":
        # Auto-add device to avoid blocking user (requested relaxation of security)
        update_user_devices(username, device_fingerprint)
        # Re-fetch user or just proceed (since we are returning tuple)
        # return None, "new_device_2fa"

    return (user['full_name'], user['role'], user['subscription_status']), "success"

def update_user_devices(username, device_fingerprint):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT known_devices FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row:
        devices = json.loads(row[0])
        if device_fingerprint not in devices:
            devices.append(device_fingerprint)
            c.execute("UPDATE users SET known_devices=? WHERE username=?", (json.dumps(devices), username))
            conn.commit()
    conn.close()

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

def get_all_users():
    """Retrieves all users with their details."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT username, full_name, role, subscription_status, trial_start_date, created_at FROM users")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_user(username):
    """Deletes a user by username."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE username=?", (username,))
        c.execute("DELETE FROM chat_history WHERE username=?", (username,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def update_user_role(username, role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE username=?", (role, username))
    conn.commit()
    conn.close()


# Initialize DB on first import
if not os.path.exists(DB_PATH):
    init_db()
