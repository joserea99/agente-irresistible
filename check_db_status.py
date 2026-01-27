import sqlite3
import os

# Identify DB Path similar to main app
if os.path.exists("/app/brain_data"):
    DB_PATH = "/app/brain_data/irresistible_app.db"
else:
    # Local fallback logic
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = "irresistible_app.db" # Assuming root for local run 
    # Or try the exact path from user metadata if known, but let's try the railway path first or local relative.
    if not os.path.exists(DB_PATH):
        # The user works in /Users/joserea/irresistible_agent
        DB_PATH = "/Users/joserea/irresistible_app.db" # Check possible location
        if not os.path.exists(DB_PATH):
             # Try inside the repo
             DB_PATH = "/Users/joserea/irresistible_agent/irresistible_app.db"

print(f"Checking DB at: {DB_PATH}")

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get latest session
    print("--- Latest Sessions ---")
    c.execute("SELECT * FROM research_sessions ORDER BY created_at DESC LIMIT 3")
    sessions = c.fetchall()
    for s in sessions:
        print(f"ID: {s['id']}, Query: {s['query']}, Status: {s['status']}, Created: {s['created_at']}")
        
        # Get assets for this session
        c.execute("SELECT status, count(*) as cnt FROM research_assets WHERE session_id=? GROUP BY status", (s['id'],))
        counts = c.fetchall()
        print("   Asset Breakdown:")
        for row in counts:
             print(f"      {row['status']}: {row['cnt']}")

    conn.close()
except Exception as e:
    print(f"Error reading DB: {e}")
