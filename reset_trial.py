
import sqlite3
from datetime import datetime
import os

DB_PATH = "/Users/joserea/irresistible_agent/irresistible_app.db"

def reset_trial():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow()
    c.execute("UPDATE users SET trial_start_date = ? WHERE username = 'testuser'", (now,))
    conn.commit()
    print("Reset trial_start_date for testuser to", now)
    conn.close()

if __name__ == "__main__":
    reset_trial()
