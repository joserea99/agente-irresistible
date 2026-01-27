
from backend.app.services.auth_service import add_user, update_user_role, init_db
import sqlite3

def setup_admin():
    username = "joserea99"
    password = "admin123"
    full_name = "Jose Rea"
    
    print(f"🔧 Setting up admin user: {username}")
    
    # ensure db exists
    init_db()
    
    # Force reset by deleting first (since we can't update password easily with current imports without direct DB access or adding a function)
    # Actually, let's just do a direct DB update for the password to be sure.
    
    conn = sqlite3.connect("irresistible_app.db")
    c = conn.cursor()
    
    # Hash password same way as auth_service
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("UPDATE users SET password_hash=?, role='admin' WHERE username=?", (pwd_hash, username))
    if c.rowcount == 0:
        # User didn't exist, create them
        add_user(username, password, full_name, "admin")
        print(f"✅ User {username} created with password '{password}'")
    else:
        conn.commit()
        print(f"✅ User {username} password reset to '{password}' and role set to 'admin'.")
    
    conn.close()

    # Also make sure testuser is admin for backup
    add_user("testuser", "testpassword", "Test User", "admin")
    update_user_role("testuser", "admin")

if __name__ == "__main__":
    setup_admin()
