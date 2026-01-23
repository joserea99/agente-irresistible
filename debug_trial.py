import sqlite3
import json
from datetime import datetime, timedelta
import os

DB_PATH = "/Users/joserea/irresistible_agent/irresistible_app.db"

def verify_logic(username):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        print("User not found")
        return
        
    print(f"User: {user['username']}")
    print(f"Trial Start Date: {user['trial_start_date']}")
    print(f"Status: {user['subscription_status']}")
    
    trial_start_str = user['trial_start_date']
    if trial_start_str:
        try:
            trial_start = datetime.strptime(trial_start_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # Try without microseconds
            trial_start = datetime.strptime(trial_start_str, '%Y-%m-%d %H:%M:%S')
            
        print(f"Parsed Trial Start: {trial_start}")
        print(f"UTC Now: {datetime.utcnow()}")
        
        diff = datetime.utcnow() - trial_start
        print(f"Diff Days: {diff.days}")
        
        days_left = 14 - diff.days
        print(f"Days Left: {days_left}")
        
        if days_left < 0:
            print("RESULT: EXPIRED")
        else:
            print("RESULT: ACTIVE")
    else:
        print("RESULT: NO DATE (ACTIVE)")

if __name__ == "__main__":
    verify_logic("testuser")
