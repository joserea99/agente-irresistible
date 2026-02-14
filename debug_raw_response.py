
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("BRANDFOLDER_API_KEY")
BRANDFOLDER_API_BASE = "https://brandfolder.com/api/v4"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def debug_response():
    # Get BF ID
    resp = requests.get(f"{BRANDFOLDER_API_BASE}/brandfolders", headers=HEADERS)
    bf_id = resp.json().get("data", [])[0]["id"]
    
    # Request Assets with per=5 to force pagination
    print("📡 Requesting assets (per=5)...")
    params = {"per": 5} 
    resp = requests.get(f"{BRANDFOLDER_API_BASE}/brandfolders/{bf_id}/assets", headers=HEADERS, params=params)
    data = resp.json()
    
    print("--- META ---")
    print(json.dumps(data.get("meta"), indent=2))
    
    print("\n--- LINKS ---")
    print(json.dumps(data.get("links"), indent=2))
    
if __name__ == "__main__":
    debug_response()
